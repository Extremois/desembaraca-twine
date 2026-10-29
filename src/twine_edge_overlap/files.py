"""Bounded read and complete, no-replace publication beside the input."""
import os
import errno
from pathlib import Path
import tempfile
from .domain.model import MAX_BYTES
from .errors import InputError,WriteError,IntegrityError


def snapshot(path):
    path=Path(path)
    if path.suffix.lower()!='.twee': raise InputError('Esta versão aceita exatamente um arquivo .twee')
    try:
        with path.open('rb') as stream: data=stream.read(MAX_BYTES+1)
    except OSError as exc: raise InputError('Não foi possível ler o arquivo; confira caminho e permissões') from exc
    if len(data)>MAX_BYTES: raise InputError('Arquivo excede o limite de 10 MiB')
    return data


def publish(source,data,validator,*,original=None):
    source=Path(source).resolve()
    temporary=None
    try:
        fd,name=tempfile.mkstemp(prefix='.twine-layout-',suffix='.tmp',dir=source.parent)
        temporary=Path(name)
        try:
            stream=os.fdopen(fd,'wb')
        except BaseException:
            os.close(fd)
            raise
        with stream:
            if stream.write(data)!=len(data): raise WriteError('Gravação incompleta')
            stream.flush(); os.fsync(stream.fileno())
        written=temporary.read_bytes()
        if written!=data: raise IntegrityError('Cópia temporária difere dos bytes validados')
        validator(written)
        if original is not None and snapshot(source)!=original: raise IntegrityError('Entrada alterada externamente durante a execução; nenhuma cópia publicada')
        for index in range(1,10001):
            suffix='' if index==1 else f'-{index}'
            destination=source.with_name(f'{source.stem}.layout{suffix}.twee')
            try:
                if os.name=='nt': os.rename(temporary,destination)
                else: os.link(temporary,destination)
                return destination
            except FileExistsError: continue
            except OSError as exc:
                if os.name!='nt' and exc.errno in (errno.EXDEV,errno.EOPNOTSUPP,errno.ENOSYS):
                    raise WriteError('O sistema de arquivos não oferece a publicação atômica necessária; nenhuma cópia gerada. Use uma pasta em sistema de arquivos com suporte a hardlinks e repita o comando.') from exc
                raise
        raise WriteError('Nomes de saída ocupados; libere um nome na pasta de entrada')
    except OSError as exc: raise WriteError('Não foi possível salvar a cópia; confira espaço e permissões na pasta de entrada') from exc
    finally:
        if temporary is not None:
            try: temporary.unlink(missing_ok=True)
            except OSError: pass
