"""Install the CLI in a private venv and expose its pip-generated launcher."""
import argparse
import ctypes
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
import venv

SOURCE_URL = 'https://github.com/Extremois/desembaraca-twine/archive/93f2699296bdc660f7bb8f57684c3a9501e3f216.zip'


def expose_windows(bin_directory):
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, 'Environment') as key:
        try:
            previous,kind=winreg.QueryValueEx(key,'Path')
        except FileNotFoundError:
            previous,kind='',winreg.REG_EXPAND_SZ
        normalize=lambda value: os.path.normcase(os.path.normpath(os.path.expandvars(value.strip('"'))))
        if normalize(str(bin_directory)) not in {normalize(value) for value in previous.split(';') if value}:
            winreg.SetValueEx(key,'Path',0,kind,previous+(';' if previous else '')+str(bin_directory))
    # Let desktop processes refresh the per-user environment for new terminals.
    result=ctypes.c_size_t()
    ctypes.windll.user32.SendMessageTimeoutW(0xffff,0x001a,0,ctypes.c_wchar_p('Environment'),2,2000,ctypes.byref(result))


def expose_posix(bin_directory,home):
    entry=shlex.quote(str(bin_directory))
    line=f'case ":$PATH:" in *:{entry}:*) ;; *) export PATH={entry}:"$PATH";; esac\n'
    profiles={home/'.profile',home/'.bashrc',home/'.zprofile',home/'.zshrc'}
    if (home/'.bash_profile').exists():profiles.add(home/'.bash_profile')
    for profile in sorted(profiles):
        existing=profile.read_bytes() if profile.exists() else b''
        if line.encode('utf-8') not in existing:
            descriptor=os.open(profile,os.O_WRONLY|os.O_APPEND|os.O_CREAT,0o600)
            with os.fdopen(descriptor,'ab') as stream:
                stream.write(b'\n# Desembaraca Twine\n'+line.encode('utf-8'))


def install(source):
    if platform.python_implementation()!='CPython' or sys.version_info[:2] not in ((3,12),(3,14)):
        raise ValueError('Use CPython 3.12 ou 3.14 nativo, com venv e pip.')
    home=Path.home()
    environment=home/'.venvs/desembaraca-twine'
    windows=os.name=='nt'
    scripts=environment/('Scripts' if windows else 'bin')
    python=scripts/('python.exe' if windows else 'python')
    if environment.exists():
        if not (environment/'pyvenv.cfg').is_file() or not python.is_file():
            raise ValueError('A pasta de instalação existente não é uma venv válida: '+str(environment))
    else:
        venv.EnvBuilder(with_pip=True).create(environment)
    env=dict(os.environ)
    for name in ('PYTHONPATH','PYTHONHOME','PIP_TARGET','PIP_PREFIX','PIP_USER'):
        env.pop(name,None)
    env.update(PIP_CONFIG_FILE=os.devnull,PYTHONNOUSERSITE='1')
    subprocess.run([str(python),'-c',
        'import platform,sys; sys.exit(0 if platform.python_implementation()=="CPython" and sys.version_info[:2] in ((3,12),(3,14)) else "A venv existente precisa usar CPython 3.12 ou 3.14.")'],check=True,env=env)
    subprocess.run([str(python),'-m','pip','install','--disable-pip-version-check','--upgrade',source],check=True,env=env)
    launcher=scripts/('desembaraca-twine.exe' if windows else 'desembaraca-twine')
    subprocess.run([str(launcher),'--help'],check=True,stdout=subprocess.DEVNULL,env=env)
    bin_directory=(Path(os.environ.get('LOCALAPPDATA') or home/'AppData/Local')/'Programs/DesembaracaTwine/bin'
                   if windows else home/'.local/bin')
    bin_directory.mkdir(parents=True,exist_ok=True)
    # pip's launcher already names the private interpreter, including Unicode paths.
    descriptor,temporary=tempfile.mkstemp(prefix='.twine-install-',dir=bin_directory)
    os.close(descriptor)
    try:
        shutil.copy2(launcher,temporary)
        os.replace(temporary,bin_directory/launcher.name)
    finally:
        Path(temporary).unlink(missing_ok=True)
    if windows:expose_windows(bin_directory)
    else:expose_posix(bin_directory,home)
    print('Instalado em '+str(environment))
    print('Feche e abra o aplicativo de terminal. Depois use: desembaraca-twine "caminho da história.twee"')
    print('Não é necessário ativar a venv. Comando disponível em '+str(bin_directory/launcher.name))


if __name__=='__main__':
    checkout=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description='Instala o comando no usuário, sem ativação manual da venv.')
    parser.add_argument('--source',default=str(checkout) if (checkout/'pyproject.toml').is_file() else SOURCE_URL,
                        help='Pacote/URL a instalar; padrão: checkout local ou revisão pública fixada.')
    try:
        install(parser.parse_args().source)
    except (OSError,ValueError,subprocess.CalledProcessError) as exc:
        parser.exit(1,'Falha na instalação: '+str(exc)+'\n')
