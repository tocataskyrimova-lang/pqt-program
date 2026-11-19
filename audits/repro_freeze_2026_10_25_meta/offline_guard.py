"""Deny network and reads/writes in original research roots during replay."""
import sys,os
from pathlib import Path
FORBIDDEN=[Path(p) for p in [r'C:\AGI\PQT',r'C:\AGI\PQT-AUDIT-001\CODEX',r'C:\AGI\PQT-AUDIT-001\HIX',r'C:\AGI\PQT-transformers']]
def install():
    def audit(event,args):
        if event in {'socket.connect','socket.getaddrinfo','urllib.Request'}:raise RuntimeError('Offline replay forbids network access')
        if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(args[0])).resolve()
            if any(p==r or r in p.parents for r in FORBIDDEN):raise RuntimeError('Replay must use frozen snapshots, not original research paths')
    sys.addaudithook(audit)
