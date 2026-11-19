"""Standard-library-only immutable bundle verification."""
from pathlib import Path
import json,hashlib,sys
root=Path(__file__).resolve().parents[1]
manifest=root/'EVIDENCE_MANIFEST.json'
if not manifest.exists():raise SystemExit('Manifest not finalized')
d=json.loads(manifest.read_text(encoding='utf-8'));bad=[]
for row in d['files']:
    p=(root/row['relative_path']).resolve()
    if root not in p.parents:bad.append({'path':row['relative_path'],'reason':'unsafe path'});continue
    if not p.is_file():bad.append({'path':row['relative_path'],'reason':'missing'});continue
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h!=row['sha256'] or p.stat().st_size!=row['size_bytes']:bad.append({'path':row['relative_path'],'reason':'size or hash mismatch'})
expected={r['relative_path'] for r in d['files']}|{'EVIDENCE_MANIFEST.json','MANIFEST.sha256'}
actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
for name in sorted(actual-expected):bad.append({'path':name,'reason':'unexpected file'})
for line in (root/'MANIFEST.sha256').read_text().splitlines():
    h,name=line.split('  ',1);p=root/name
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:bad.append({'path':name,'reason':'outer manifest digest mismatch'})
out={'checked_payload_files':len(d['files']),'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'bad':bad,'status':'PASS' if not bad else 'FAIL'}
print(json.dumps(out,indent=2));raise SystemExit(bool(bad))
