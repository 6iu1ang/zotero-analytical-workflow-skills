"""Create reproducible distributable archives from an explicit file scope."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / 'scripts/check_package.py')], check=True)
DIST = ROOT / 'dist'
DIST.mkdir(exist_ok=True)

def archive(out, files, base):
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(files):
            info = zipfile.ZipInfo(path.relative_to(base).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, path.read_bytes())

def resources(directory):
    return [p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts]

for skill in sorted((ROOT / 'skills').iterdir()):
    if skill.is_dir():
        archive(DIST / (skill.name + '.skill'), resources(skill), skill.parent)
files = [ROOT / x for x in ['README.md', 'requirements.txt', 'config.example.json', '.gitignore', '.gitattributes']]
for directory in ['skills', 'scripts', 'tests', '.github']:
    files += resources(ROOT / directory)
archive(DIST / 'zotero-analytical-workflow-skills.zip', files, ROOT)
manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DIST.iterdir()) if p.suffix in {'.skill', '.zip'}}
(DIST / 'SHA256SUMS.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(f'Created {len(manifest)} archives in {DIST}')
