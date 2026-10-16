"""Bounded process runner for layout experiments, independent of production code."""

from dataclasses import dataclass
import math
import queue
import subprocess
import threading
import time
from typing import Sequence


class ProcessLimitError(RuntimeError):
    """An experimental process exceeded its time or output allowance."""


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def run_bounded(
    command: Sequence[str], *, timeout: float = 30.0, max_output: int = 8 * 1024 * 1024
) -> ProcessResult:
    """Run a direct executable, retaining at most max_output combined bytes.

    Experimental commands must not spawn helpers. Both supported probe commands below
    run directly, without shell, Node workers or wrappers. This does not claim general
    process-tree containment for arbitrary commands.
    """
    if not math.isfinite(timeout) or timeout <= 0 or max_output < 0:
        raise ValueError("Invalid experimental process allowance")
    deadline = time.monotonic() + timeout
    process = subprocess.Popen(
        list(command), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=False,
    )
    chunks: queue.Queue[tuple[int, bytes | None]] = queue.Queue(maxsize=16)
    stopped = threading.Event()

    def enqueue(value: tuple[int, bytes | None]) -> None:
        while not stopped.is_set():
            try:
                chunks.put(value, timeout=0.05)
                return
            except queue.Full:
                pass

    def read_pipe(index, pipe) -> None:
        try:
            with pipe:
                while not stopped.is_set():
                    chunk = pipe.read1(8192)
                    if not chunk:
                        break
                    enqueue((index, chunk))
        finally:
            enqueue((index, None))

    threads = [
        threading.Thread(target=read_pipe, args=(i, pipe), daemon=True)
        for i, pipe in enumerate((process.stdout, process.stderr))
    ]
    for thread in threads:
        thread.start()
    output = [bytearray(), bytearray()]
    total, finished = 0, 0
    try:
        while finished < 2:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProcessLimitError("Experimental time allowance exceeded")
            try:
                index, chunk = chunks.get(timeout=min(0.05, remaining))
            except queue.Empty:
                continue
            if chunk is None:
                finished += 1
                continue
            total += len(chunk)
            if total > max_output:
                raise ProcessLimitError("Experimental combined output allowance exceeded")
            output[index].extend(chunk)
        try:
            code = process.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired as exc:
            raise ProcessLimitError("Experimental time allowance exceeded") from exc
        return ProcessResult(code, bytes(output[0]), bytes(output[1]))
    finally:
        stopped.set()
        cleanup_deadline = time.monotonic() + 2
        if process.poll() is None:
            process.kill()
        process.wait(timeout=max(0.01, cleanup_deadline - time.monotonic()))
        for thread in threads:
            thread.join(timeout=max(0, cleanup_deadline - time.monotonic()))
