#!/usr/bin/python3
"""Check the installed rEFInd; restore only a pinned, verified backup."""
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

STATE=Path('/var/lib/refind-integrity')
TARGET=Path('/boot/efi/EFI/refind/grubx64.efi')
ESP_PARTUUID='ea60226c-d140-48e6-aeaa-eb477587c6f1'

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(path):
    """Read only: check PE certificate bounds and trusted signing certificate."""
    try:
        data=path.read_bytes()
        if data[:2]!=b'MZ': return False,'the EFI executable has no valid PE header'
        pe=struct.unpack_from('<I',data,0x3c)[0]
        if data[pe:pe+4]!=b'PE\0\0': return False,'the EFI executable has an invalid PE signature'
        optional=pe+24
        if struct.unpack_from('<H',data,optional)[0]!=0x20b:
            return False,'the executable is not a 64-bit PE image'
        offset,size=struct.unpack_from('<II',data,optional+112+4*8)
        if not offset or size<8 or offset+size>len(data):
            return False,'the Secure Boot signature data is missing or truncated'
        result=subprocess.run(['/usr/bin/sbverify','--cert',str(STATE/'certificate.crt'),str(path)],
            capture_output=True,text=True,timeout=10)
        if result.returncode:
            return False,'the Secure Boot signature does not match the trusted certificate'
        return True,'signature and PE certificate bounds verified'
    except (OSError,ValueError,struct.error,subprocess.SubprocessError) as error:
        return False,f'could not verify the EFI executable: {error}'

def mounted_esp():
    result=subprocess.run(['/usr/bin/findmnt','-no','SOURCE','--target','/boot/efi'],
        capture_output=True,text=True,check=True,timeout=5)
    device=result.stdout.strip()
    result=subprocess.run(['/usr/bin/lsblk','-no','PARTUUID',device],
        capture_output=True,text=True,check=True,timeout=5)
    if result.stdout.strip()!=ESP_PARTUUID:
        raise RuntimeError('EFI partition does not match this machine; no repair attempted')

def record(status,message,recovery=None):
    old={}
    status_path=STATE/'status.json'
    if status_path.exists(): old=json.loads(status_path.read_text())
    payload=dict(status=status,message=message,checked_at=now(),
                 last_recovery=recovery or old.get('last_recovery'))
    temporary=STATE/'status.json.new'
    temporary.write_text(json.dumps(payload,indent=2)+'\n')
    temporary.chmod(0o644)
    temporary.replace(status_path)
    print(message,flush=True)
    return payload

def check():
    mounted_esp()
    valid,reason=verify(TARGET)
    if valid:
        record('healthy','rEFInd is ready: its Secure Boot signature is valid.')
        return 0
    manifest=json.loads((STATE/'trusted-backup.json').read_text())
    backup=STATE/'known-good.efi'
    backup_valid,backup_reason=verify(backup)
    if not backup_valid or sha(backup)!=manifest['sha256']:
        record('error',f'rEFInd needs attention: {reason}. The recovery copy is not trusted '
            f'({backup_reason}). No EFI files were changed. Use F12 to select Bazzite or Windows; '
            'do not disable Secure Boot. See journalctl -u refind-integrity.service.')
        return 2
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    quarantine=STATE/'quarantine'
    quarantine.mkdir(mode=0o700,exist_ok=True)
    if TARGET.exists():
        broken=quarantine/(stamp+'.efi')
        broken.write_bytes(TARGET.read_bytes());broken.chmod(0o600)
    temporary=TARGET.with_name('grubx64.integrity-recovery.tmp')
    try:
        temporary.write_bytes(backup.read_bytes())
        replacement_valid,_=verify(temporary)
        if not replacement_valid or sha(temporary)!=manifest['sha256']:
            raise RuntimeError('staged recovery file failed verification; original retained')
        with temporary.open('rb') as handle: os.fsync(handle.fileno())
        temporary.replace(TARGET)
        os.sync()
        if not verify(TARGET)[0]: raise RuntimeError('restored file failed final verification')
    finally:
        temporary.unlink(missing_ok=True)
    message=(f'rEFInd was repaired automatically: {reason}. Restored the original verified '
        'signed boot manager. Your theme and OS entries are preserved; Secure Boot and '
        'firmware boot order were not changed.')
    record('repaired',message,dict(at=now(),reason=reason,message=message))
    return 0

def main():
    action=sys.argv[1] if len(sys.argv)>1 else 'status'
    if action=='status':
        path=STATE/'status.json'
        if not path.exists(): sys.exit('No check has been recorded yet.')
        status=json.loads(path.read_text())
        print(status['message'])
        print('Last check:',status['checked_at'])
        if status.get('last_recovery'):
            print('Last automatic repair:',status['last_recovery']['at'])
        print('Details: journalctl -u refind-integrity.service')
        return
    if action!='check': sys.exit('Usage: integrity-guard.py [status|check]')
    if os.geteuid()!=0: sys.exit('Use sudo to check and repair the boot manager.')
    with open('/run/refind-integrity.lock','w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try: result=check()
        except Exception as error:
            record('error',f'rEFInd check could not complete: {error}. Use F12 for the original '
                'Bazzite or Windows entry if needed. See journalctl -u refind-integrity.service.')
            result=2
    sys.exit(result)

if __name__=='__main__': main()
