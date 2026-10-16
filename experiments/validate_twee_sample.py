"""Characterize the received simple Twee sample and verify one position-only edit.

This deliberately narrow experiment is not the production parser or a layout engine.
It accepts plain passage names, flat position/size metadata and simple [[target]] links.
The output is a disposable local copy for import validation, not an optimized graph.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re


HEADER = re.compile(rb"^:: ([^\r\n]+)\r?$", re.MULTILINE)
NARRATIVE = re.compile(rb"(?P<name>[^{}\[\]\r\n]+?) (?P<meta>\{[^\r\n]*\})$")
POSITION = re.compile(rb'"position"\s*:\s*"(?P<value>[^"\\]*)"')


def inspect(data: bytes) -> tuple[list[tuple[int, int]], list[str], list[str]]:
    data.decode("utf-8", errors="strict")
    headers = list(HEADER.finditer(data))
    if not headers or data[: headers[0].start()].strip():
        raise ValueError("Expected a Twee header at the beginning of the sample")
    spans, names, targets = [], [], []
    special = set()
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(data)
        body = data[header.end() : end]
        label = header.group(1).decode("utf-8")
        if label in {"StoryTitle", "StoryData"}:
            if label in special:
                raise ValueError("Duplicate special passage")
            special.add(label)
            if label == "StoryData":
                json.loads(body)
            continue
        narrative = NARRATIVE.fullmatch(header.group(1))
        if narrative is None:
            raise ValueError("Header outside the narrow experimental profile")
        metadata = json.loads(narrative.group("meta"))
        if set(metadata) != {"position", "size"}:
            raise ValueError("Unexpected metadata in the experimental profile")
        for key in ("position", "size"):
            numbers = [float(value) for value in metadata[key].split(",")]
            if len(numbers) != 2 or not all(math.isfinite(value) for value in numbers):
                raise ValueError("Invalid coordinates or size")
            if key == "size" and not all(value > 0 for value in numbers):
                raise ValueError("Nonpositive size")
        position = POSITION.search(narrative.group("meta"))
        if position is None:
            raise ValueError("No patchable position value")
        offset = header.start(1) + narrative.start("meta")
        spans.append((offset + position.start("value"), offset + position.end("value")))
        names.append(narrative.group("name").decode("utf-8"))
        for target in re.findall(rb"\[\[([^\]\r\n]+)\]\]", body):
            if any(token in target for token in (b"->", b"<-", b"|", b"[")):
                raise ValueError("Link syntax outside the simple sample profile")
            targets.append(target.decode("utf-8"))
    if len(names) != len(set(names)) or any(target not in names for target in targets):
        raise ValueError("Duplicate names or missing link targets")
    if special != {"StoryTitle", "StoryData"} or not spans:
        raise ValueError("Missing story metadata or narrative passages")
    return spans, names, targets


def neutralize(data: bytes, spans: list[tuple[int, int]]) -> bytes:
    parts, previous = [], 0
    for start, end in spans:
        parts.extend((data[previous:start], b"<POSITION>"))
        previous = end
    parts.append(data[previous:])
    return b"".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    original = args.source.read_bytes()
    spans, names, targets = inspect(original)
    start, end = spans[0]
    x, y = original[start:end].decode("ascii").split(",")
    replacement = f"{float(x) + 10:g},{y}".encode("ascii")
    candidate = original[:start] + replacement + original[end:]
    candidate_spans, candidate_names, candidate_targets = inspect(candidate)
    if neutralize(original, spans) != neutralize(candidate, candidate_spans):
        raise ValueError("Bytes outside position values changed")
    if (names, targets) != (candidate_names, candidate_targets):
        raise ValueError("Names or connections changed")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as output:
        output.write(candidate)
    if args.output.read_bytes() != candidate or args.source.read_bytes() != original:
        raise ValueError("Output verification or original preservation failed")
    print(json.dumps({
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "output_sha256": hashlib.sha256(candidate).hexdigest(),
        "passages": len(names), "links": len(targets),
        "all_bytes_outside_positions_preserved": True,
        "changed_positions": 1, "original_unchanged": True,
        "purpose": "import-validation-only; not optimized",
        "output": str(args.output.resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()
