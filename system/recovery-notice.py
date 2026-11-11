#!/usr/bin/python3
"""Notify the logged-in user once after a repair, or once per check failure."""
import json
import os
from pathlib import Path
import subprocess

try:
    status=json.loads(Path('/var/lib/refind-integrity/status.json').read_text())
    event=status if status['status']=='error' else status.get('last_recovery')
    if event:
        token=event.get('at') or event['checked_at']
        state=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'refind'
        marker=state/'recovery-notified'
        if not marker.exists() or marker.read_text()!=token:
            subprocess.run(['/usr/bin/notify-send','--app-name=Boot manager',
                '--icon=computer','--urgency=normal' if status['status']!='error' else '--urgency=critical',
                'Boot manager repaired' if status['status']!='error' else 'Boot manager needs attention',
                event['message']],check=True,timeout=10)
            state.mkdir(parents=True,exist_ok=True)
            marker.write_text(token)
except (OSError,KeyError,ValueError,subprocess.SubprocessError):
    pass
