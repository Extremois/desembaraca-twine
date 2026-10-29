"""Query KVM on disposable GitHub Linux runners; never create or boot a VM."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import struct
import sys

# Linux uapi/linux/kvm.h: _IO(KVMIO, 0x00), _IO(KVMIO, 0x03), KVM_CAP_USER_MEMORY.
KVM_GET_API_VERSION=0xAE00
KVM_CHECK_EXTENSION=0xAE03
KVM_CAP_USER_MEMORY=3


def query_status(api,user_memory):
    if api!=12:return 'api-mismatch'
    return 'query-ready' if user_memory>0 else 'extension-unavailable'


def probe_device(device=Path('/dev/kvm')):
    result=dict(status='not-present',device_present=False,device_opened=False,
                api_version=None,user_memory=None,no_vm_created=True,no_guest_executed=True)
    try:
        info=device.lstat()
        result['device_present']=True
        result['device_mode']=stat.S_IMODE(info.st_mode)
        if not stat.S_ISCHR(info.st_mode):
            result['status']='not-character-device';return result
        descriptor=os.open(device,os.O_RDWR|getattr(os,'O_CLOEXEC',0)|getattr(os,'O_NOFOLLOW',0))
        try:
            if not stat.S_ISCHR(os.fstat(descriptor).st_mode):
                result['status']='not-character-device';return result
            result['device_opened']=True
            import fcntl
            result['api_version']=fcntl.ioctl(descriptor,KVM_GET_API_VERSION,0)
            if result['api_version']==12:
                result['user_memory']=fcntl.ioctl(descriptor,KVM_CHECK_EXTENSION,KVM_CAP_USER_MEMORY)
            result['status']=query_status(result['api_version'],result['user_memory'])
        finally:os.close(descriptor)
    except FileNotFoundError:
        result['status']='not-present'
    except PermissionError as error:
        result.update(status='access-denied',errno=error.errno)
    except OSError as error:
        result.update(status='device-or-ioctl-error',errno=error.errno)
    return result


def main(report):
    expected={'X64':'x86_64','ARM64':'aarch64'}.get(os.environ.get('RUNNER_ARCH'))
    if (os.environ.get('GITHUB_ACTIONS')!='true' or sys.platform!='linux'
            or expected is None or platform.machine()!=expected or struct.calcsize('P')!=8):
        raise ValueError('Requires a matching 64-bit GitHub-hosted Linux runner')
    result=dict(kind='github-kvm-api-preflight-not-guest-execution',qualified=False,approved=False,
        revision=os.environ.get('GITHUB_SHA'),arch=platform.machine(),kernel=platform.release(),
        runner_image=os.environ.get('ImageOS'),runner_image_version=os.environ.get('ImageVersion'),
        elevated=os.geteuid()==0,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        probe=probe_device(),
        scope='API/access query only; guest boot, acceleration, guest kernel and distribution acceptance remain untested',
        references=['https://docs.kernel.org/virt/kvm/api.html#kvm-get-api-version',
                    'https://docs.github.com/en/actions/reference/runners/github-hosted-runners'])
    with report.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(platform.machine(), 'elevated' if result['elevated'] else 'runner-user',result['probe']['status'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    main(parser.parse_args().report)
