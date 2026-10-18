"""Coordinate the local use case; all published data is revalidated."""
from pathlib import Path
import time
from .domain.model import GLOBAL_SECONDS,Result
from .domain.geometry import measure
from .domain.selection import choose
from .domain.result import classify
from .engines import graphviz
from .errors import EngineError,BudgetError,IntegrityError
from .files import snapshot,publish
from .formats.profile import parse,serialize,verify
from .runtime import ensure_runtime


def run(path,*,engine=None,seconds=GLOBAL_SECONDS,runtime_provider=None,progress=None):
    deadline=time.monotonic()+seconds
    source=Path(path).resolve()
    source_bytes=snapshot(source)
    original=parse(source_bytes,deadline)
    preparation_start=time.monotonic()
    runtime=(runtime_provider() if runtime_provider is not None else ensure_runtime(progress=progress))
    preparation_elapsed=time.monotonic()-preparation_start
    # Acquisition is excluded, but local host/snapshot classification consumes the
    # existing processing allowance. Injected providers keep their old contract.
    classification=max(0.0,min(preparation_elapsed,getattr(runtime,'classification_seconds',0.0)))
    deadline+=preparation_elapsed-classification
    try:
        if time.monotonic()>=deadline:
            raise TimeoutError()
        before=measure(original,deadline)
    except TimeoutError as exc:
        raise BudgetError('Prazo global esgotado antes de validar a disposição original; nenhuma cópia gerada') from exc
    chosen=original; after=before
    reason='Não havia conflitos a resolver' if before.clean else 'Nenhuma melhoria admissível; layout original preservado'
    if not before.clean:
        try:
            positions=engine(original,deadline) if engine is not None else graphviz.layout(original,deadline,runtime=runtime)
            if time.monotonic()>=deadline:
                raise TimeoutError()
            candidate=parse(serialize(original,positions),deadline)
            verify(original,candidate)
            candidate_metrics=measure(candidate,deadline)
            chosen=choose(original,candidate,before,candidate_metrics)
            if chosen is candidate:
                after=candidate_metrics
                reason=('Layout melhorado' if after.clean else 'Melhoria parcial')+' sem aumentar nenhuma das três contagens'
            else: reason='Nenhuma melhoria admissível: candidato empatado ou com regressão; layout original preservado'
        except TimeoutError:
            reason='Prazo global de processamento esgotado; layout original preservado'
        except EngineError as exc:
            reason=f'Limitação do motor: {exc}; layout original preservado'
    def validate(data):
        candidate=parse(data)
        verify(original,candidate)
        # Bytes must be exactly those whose serialized geometry was selected.
        if data!=chosen.raw: raise IntegrityError('Cópia difere do candidato selecionado')
    output=publish(source,chosen.raw,validate,original=source_bytes)
    if original.layout_initialized:
        reason+='; layout inicial e dimensões ausentes definidos conforme o importador do Twine, somente na cópia'
    if chosen.opaque: reason+='; scripts/estilos ou macros opacos: análise apenas das conexões estáticas reconhecidas'
    status=classify(after,opaque=chosen.opaque)
    return Result(status,output,before,after,reason)
