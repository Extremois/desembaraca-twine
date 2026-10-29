"""Exercise the installer only on disposable GitHub Actions runners."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]


def collect(wheel):
    if os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('Run installer acceptance in GitHub Actions')
    windows=os.name=='nt'
    if windows:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,'Environment') as key:
            try:previous=winreg.QueryValueEx(key,'Path')
            except FileNotFoundError:previous=None
    try:
        with tempfile.TemporaryDirectory(prefix='twine install ação ') as temporary:
            work=Path(temporary);home=work/'perfil com espaços';home.mkdir()
            env=dict(os.environ,HOME=str(home),USERPROFILE=str(home),LOCALAPPDATA=str(home/'local'),
                     PYTHONUTF8='1',PIP_NO_INDEX='1',PIP_DISABLE_PIP_VERSION_CHECK='1')
            # A standalone downloaded installer must not depend on the checkout.
            installer=work/'install.py';shutil.copy2(ROOT/'install.py',installer)
            binary=home/('local/Programs/DesembaracaTwine/bin/desembaraca-twine.exe' if windows else '.local/bin/desembaraca-twine')
            def run(command,environment=env):
                return subprocess.run([str(x) for x in command],cwd=home,env=environment,check=True,
                                      capture_output=True,timeout=180)
            for _ in range(2):run([sys.executable,installer,'--source',wheel])
            assert binary.is_file()
            profiles={}
            if windows:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as key:
                    current,kind=winreg.QueryValueEx(key,'Path')
                added=str(binary.parent)
                expected=(previous[0]+(';' if previous[0] else '') if previous else '')+added
                assert current==expected and current.split(';').count(added)==1
                clean=dict(env,PATH=added+os.pathsep+str(Path(os.environ['SystemRoot'])/'System32'))
                powershell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
                resolved=run([powershell,'-NoProfile','-NonInteractive','-Command',
                    '[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); (Get-Command desembaraca-twine).Source; desembaraca-twine --help'],clean).stdout.decode('utf-8').strip()
                assert Path(resolved.splitlines()[0]).samefile(binary)
            else:
                for name in ('.profile','.bashrc','.zprofile','.zshrc'):
                    profile=home/name;raw=profile.read_bytes();assert raw.count(b'# Desembaraca Twine')==1
                    profiles[name]=hashlib.sha256(raw).hexdigest()
                clean=dict(env,PATH='/usr/bin:/bin')
                run(['/bin/sh','-c','. "$HOME/.profile"; command -v desembaraca-twine; desembaraca-twine --help'],clean)
                if Path('/bin/bash').is_file():run(['/bin/bash','--noprofile','-ic','desembaraca-twine --help'],clean)
                if Path('/bin/zsh').is_file():run(['/bin/zsh','-ic','desembaraca-twine --help'],clean)
            # Argument boundaries survive spaces, accents and shell metacharacters.
            result=subprocess.run(
                [str(binary),'arquivo com ação & porcentagem % inexistente.twee'],cwd=home,env=env,capture_output=True,timeout=30)
            assert result.returncode==1 and 'Não foi possível ler o arquivo' in result.stderr.decode('utf-8')
            assert not list(home.rglob('ready.json'))
            return dict(passed=True,revision=os.environ['GITHUB_SHA'],system=platform.system(),python=platform.python_version(),
                        outside_checkout=True,standalone_installer=True,rerun_idempotent=True,activation_required=False,
                        private_launcher=True,argument_boundaries=True,existing_path_preserved=True,
                        profile_hashes=profiles,runtime_prepared=False)
    finally:
        if windows:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,'Environment') as key:
                if previous is None:winreg.DeleteValue(key,'Path')
                else:winreg.SetValueEx(key,'Path',0,previous[1],previous[0])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    args.report.write_text(json.dumps(collect(args.wheel.resolve()),indent=2)+'\n',encoding='utf-8')
