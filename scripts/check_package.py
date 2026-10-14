"""Validate publishable skill resources without loading personal artifacts."""
from pathlib import Path
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
errors = []
names = {p.name for p in (ROOT / 'skills').iterdir() if p.is_dir()}
expected = {'research-vault-ingest-orchestrator', 'zotero-collection-manager', 'zotero-data-fetcher', 'zotero-analytical-writer', 'research-vault-knowledge-maintainer'}
if names != expected:
    errors.append('Unexpected skill set')
for name in sorted(names):
    path = ROOT / 'skills' / name / 'SKILL.md'
    text = path.read_text(encoding='utf-8')
    match = re.match(r'^---\n(.*?)\n---', text, re.S)
    fm = yaml.safe_load(match[1]) if match else {}
    if fm.get('name') != name or not fm.get('description') or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or len(name) > 64:
        errors.append(f'{name}: invalid skill frontmatter')
    ui = yaml.safe_load((path.parent / 'agents/openai.yaml').read_text(encoding='utf-8'))['interface']
    if not 25 <= len(ui['short_description']) <= 64 or '$' + name not in ui['default_prompt']:
        errors.append(f'{name}: invalid UI metadata')
for path in ROOT.rglob('*'):
    if not path.is_file() or any(x in path.relative_to(ROOT).parts for x in ['.git', '.validation', '__pycache__', 'dist', 'local']):
        continue
    if path.suffix.lower() in {'.pdf', '.sqlite', '.jsonl', '.png'} or path.name == 'config.json':
        errors.append(f'Non-publishable artifact: {path.relative_to(ROOT)}')
    if path.suffix in {'.md', '.json', '.yaml', '.py', '.txt'}:
        text = path.read_text(encoding='utf-8')
        if re.search(r'(?:E:|C:)\\|(?:E:|C:)/Users|gh[pousr]_[A-Za-z0-9]{20,}', text):
            errors.append(f'Personal path, paper identity or credential in {path.relative_to(ROOT)}')
        if path.suffix == '.md':
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if '://' in target or target.startswith('#'):
                    continue
                target = target.split('#', 1)[0]
                if target and not (path.parent / target).exists():
                    errors.append(f'Broken relative resource: {path.relative_to(ROOT)} -> {target}')
            if path.parent.name == '知识库模板':
                if 'mechanistic' in text or ' / counter' in text or 'evidence_status: "note_supported"' in text:
                    errors.append(f'Frozen schema mismatch in {path.name}')
if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
print(f'PASS: {len(names)} skills, UI metadata, resource links, template enums and publication scope')
