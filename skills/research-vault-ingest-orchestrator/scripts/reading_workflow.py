"""Read-only Zotero materials, source checks, and append-only reading records.

This helper never writes Zotero, generates scientific notes, or certifies
context/figure review. Those are explicit agent responsibilities.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

from pypdf import PdfReader
import yaml

HEADINGS = ['基本信息', '一句话摘要', '研究对象', '研究方法', '数据来源', '研究结论', '关联精读笔记', '我的判断']
NOTE_FIELDS = ['title', 'aliases', 'tags', 'created', 'source', 'author', 'year', 'theme', 'study_area', 'data_source', 'methodology', 'core_variable', 'key_finding', 'relevance', 'source_type', 'source_file', 'source_sha256', 'note_path']
KEY_RE = re.compile(r'^[A-Z0-9]{8}$')
TERMINAL = {'COMPLETE', 'ALREADY_COMPLETE'}
STATES = TERMINAL | {'PDF_NOT_FOUND', 'PDF_UNREADABLE', 'KEY_CONFLICT', 'PARTIAL_NOTE_MISSING', 'VALIDATION_FAILED', 'MANUAL_REVIEW_REQUIRED', 'SCHEMA_REVIEW_REQUIRED'}


def digest(path):
    with Path(path).open('rb') as stream:
        h = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
        return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def config(path):
    path = Path(path).resolve()
    c = read_json(path)
    for key in ['vault_root', 'zotero_data_dir', 'work_dir', 'process_log']:
        if not c.get(key):
            raise ValueError(f'Missing config field: {key}')
        p = Path(os.path.expandvars(c[key])).expanduser()
        c[key] = p.resolve() if p.is_absolute() else (path.parent / p).resolve()
    c.setdefault('zotero_api_base', 'http://127.0.0.1:23119/api/users/0')
    if not c['vault_root'].is_dir() or not c['zotero_data_dir'].is_dir():
        raise ValueError('Configure existing Vault and Zotero data directories first')
    return c


class Zotero:
    def __init__(self, base):
        parts = urllib.parse.urlsplit(base)
        if parts.scheme not in {'http', 'https'} or parts.username or parts.password:
            raise ValueError('Use a plain HTTP(S) Zotero API base without credentials')
        if parts.hostname not in {'localhost', '127.0.0.1', '::1'}:
            raise ValueError('This helper supports the local API; use a connected tool for other libraries')
        self.base = base.rstrip('/')
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def get(self, route):
        with self.opener.open(self.base + '/' + route, timeout=30) as response:
            return json.loads(response.read())

    def all(self, route):
        out, start = [], 0
        sep = '&' if '?' in route else '?'
        while True:
            batch = self.get(f'{route}{sep}limit=100&start={start}')
            if not isinstance(batch, list):
                raise ValueError('Expected an API item list')
            out.extend(batch)
            if len(batch) < 100:
                return out
            start += len(batch)


def note_fields(path):
    text = Path(path).read_text(encoding='utf-8-sig')
    m = re.match(r'^---\s*\n(.*?)\n---(?:\n|$)', text, re.S)
    if not m:
        raise ValueError('Missing YAML frontmatter')
    fields = yaml.safe_load(m[1])
    if not isinstance(fields, dict):
        raise ValueError('Frontmatter must be a mapping')
    return fields, text[m.end():]


def existing_notes(vault):
    out = {}
    for path in Path(vault).rglob('*.md'):
        if '.meta' in path.parts:
            continue
        try:
            fields, _ = note_fields(path)
        except (ValueError, yaml.YAMLError, UnicodeError):
            continue
        if fields.get('type') == 'literature-note' or 'literature-note' in fields.get('tags', []):
            key = fields.get('zotero_key')
            if key:
                out.setdefault(key, []).append(path.relative_to(vault).as_posix())
    return out


def attachment_path(data_dir, item):
    d = item['data']
    if d.get('linkMode') == 'linked_file':
        raw = d.get('path', '')
        # Zotero's attachments: relative linked-file base requires a separate resolver.
        if raw and Path(raw).is_absolute():
            return Path(raw)
        return None
    name = d.get('filename') or d.get('path', '').removeprefix('storage:')
    if not name or Path(name).name != name or '/' in name or '\\' in name:
        return None
    return Path(data_dir) / 'storage' / item['key'] / name


def material_for(api, item, c, notes):
    if item['data'].get('itemType') in {'attachment', 'note', 'annotation'} or item['data'].get('parentItem'):
        raise ValueError('Select a parent bibliographic item, not an attachment')
    key = item['key']
    children = api.all(f'items/{key}/children')
    collections = [api.get(f'collections/{k}') for k in item['data'].get('collections', [])]
    pdfs = []
    for child in children:
        d = child['data']
        if d.get('contentType') != 'application/pdf':
            continue
        if d.get('parentItem') != key:
            raise ValueError('PDF parent identity conflict')
        path = attachment_path(c['zotero_data_dir'], child)
        p = {'pdf_key': child['key'], 'pdf_path': str(path) if path else '', 'exists': bool(path and path.is_file()), 'readable': False}
        if p['exists']:
            p['source_sha256'] = digest(path)
            try:
                reader = PdfReader(path)
                p['page_count'] = len(reader.pages)
                p['readable'] = bool(reader.pages)
                if not p['readable']:
                    p['error'] = 'PDF has no pages'
            except Exception as exc:
                p['error'] = type(exc).__name__
            p['cache_exists'] = (path.parent / '.zotero-ft-cache').is_file()
        p['annotations'] = api.all(f'items/{child["key"]}/children')
        pdfs.append(p)
    return {'zotero_key': key, 'item': item, 'collections': collections, 'children': children, 'pdfs': pdfs, 'existing_notes': notes.get(key, [])}


def select_items(api, args):
    if args.key:
        if not KEY_RE.fullmatch(args.key):
            raise ValueError('Invalid parent key')
        return [api.get(f'items/{args.key}')], []
    if args.title:
        matches = api.all('items/top?q=' + urllib.parse.quote(args.title))
        matches = [x for x in matches if x['data'].get('title', '').casefold().strip() == args.title.casefold().strip()]
        if len(matches) != 1:
            raise ValueError(f'Title has {len(matches)} exact candidates; select a parent key')
        return matches, []
    collections = api.all('collections')
    selected = [x for x in collections if x['key'] == args.collection] if args.collection else [x for x in collections if x['data']['name'] == args.collection_name]
    if len(selected) != 1:
        raise ValueError(f'Collection has {len(selected)} candidates; use its key')
    keys = {selected[0]['key']}
    if args.include_subcollections:
        while True:
            added = {x['key'] for x in collections if x['data'].get('parentCollection') in keys}
            if added <= keys:
                break
            keys |= added
    items = {}
    for key in sorted(keys):
        for item in api.all(f'collections/{key}/items/top'):
            if item['data'].get('itemType') not in {'attachment', 'note', 'annotation'}:
                items[item['key']] = item
    return list(items.values()), sorted(keys)


def normalized(s):
    # Ignore PDF line wrapping/hyphenation, while retaining meaningful signs.
    s = re.sub(r'(?<=[A-Za-z])[-‐]\s*\n\s*(?=[A-Za-z])', '', s)
    s = re.sub(r'(?<=[A-Za-z])[-‐](?=[A-Za-z])', '', s)
    s = s.replace('\x00', '-').replace('−', '-').replace('‐', '-').replace('\u00ad', '')
    return re.sub(r'\s+', '', s)


def validate_note(note, vault, review, material=None):
    errors, checks = [], []

    def test(name, ok):
        checks.append({'check': name, 'passed': bool(ok)})
        if not ok:
            errors.append(name)

    note, vault = Path(note).resolve(), Path(vault).resolve()
    try:
        relative = note.relative_to(vault).as_posix()
        f, body = note_fields(note)
    except (ValueError, OSError, yaml.YAMLError) as exc:
        return {'passed': False, 'errors': [str(exc)], 'checks': checks}
    test('template-fields', all(k in f for k in NOTE_FIELDS))
    test('literature-note', f.get('type') == 'literature-note' or 'literature-note' in f.get('tags', []))
    test('note-path', f.get('note_path') == relative)
    test('template-heading-order', re.findall(r'^## (.+)$', body, re.M) == HEADINGS)
    test('method-subsections', '### 方法概述' in body and '### 方法分析' in body)
    test('no-placeholders', not any(s in body for s in ['{{', '在此粘贴', '按需继续补充', '[[]]']))
    test('math-delimiters', body.count('$$') % 2 == 0 and len(re.findall(r'(?<!\\)\$', body.replace('$$', ''))) % 2 == 0)
    source = Path(f.get('source_file') or '')
    test('source-is-absolute-pdf', source.is_absolute() and source.suffix.lower() == '.pdf')
    test('source-exists', source.is_file())
    if not source.is_file():
        return {'passed': False, 'errors': errors, 'checks': checks}
    actual_hash = digest(source)
    test('source-hash', actual_hash == f.get('source_sha256') == review.get('source_sha256'))
    try:
        pages = [pg.extract_text() or '' for pg in PdfReader(source).pages]
    except Exception as exc:
        test('source-readable', False)
        return {'passed': False, 'errors': errors + [type(exc).__name__], 'checks': checks}
    test('source-readable', bool(pages))
    zotero_mode = f.get('source_type') == 'zotero_pdf'
    if zotero_mode:
        test('confirmed-zotero-identity', bool(KEY_RE.fullmatch(str(f.get('zotero_key', ''))) and KEY_RE.fullmatch(str(f.get('pdf_key', '')))))
        test('parent-pdf-links', f'zotero://select/library/items/{f.get("zotero_key")}' in body and f'zotero://open-pdf/library/items/{f.get("pdf_key")}' in body)
        test('parent-unique-in-vault', existing_notes(vault).get(f.get('zotero_key')) == [relative])
        test('material-required-for-zotero', material is not None)
        if material:
            test('material-parent-title', material.get('zotero_key') == f.get('zotero_key') and material['item']['data']['title'] == f.get('title'))
            matches = [p for p in material['pdfs'] if p['pdf_key'] == f.get('pdf_key')]
            test('material-attachment-source', len(matches) == 1 and Path(matches[0]['pdf_path']).resolve() == source.resolve() and matches[0].get('source_sha256') == actual_hash)
            test('doi-identity', f.get('doi', '') == material['item']['data'].get('DOI', ''))
    else:
        test('pdf-only-no-invented-keys', not f.get('zotero_key') and not f.get('pdf_key'))
        test('pdf-only-source-link', source.as_posix() in body or str(source) in body or source.as_uri() in body)
    test('original-context-reviewed', review.get('context_verified') is True)
    for aspect in ['formulas', 'figures']:
        r = review.get(aspect, {})
        applicable = r.get('applicable')
        test(aspect + '-review', applicable is False or (applicable is True and r.get('verified') is True and bool(r.get('pages')) and all(isinstance(n, int) and 1 <= n <= len(pages) for n in r['pages'])))
    conclusion = body.split('## 研究结论', 1)[-1].split('## 关联精读笔记', 1)[0]
    blocks = re.split(r'(?=^- \*\*主要发现 \d+\*\*)', conclusion, flags=re.M)[1:]
    quotes = review.get('quotes', [])
    test('finding-quote-coverage', bool(blocks) and len(blocks) == len(quotes))
    seen = set()
    for q in quotes:
        i, page, quote = q.get('finding_number'), q.get('page'), q.get('quote', '')
        test('quote-number-unique', isinstance(i, int) and 1 <= i <= len(blocks) and i not in seen)
        if not isinstance(i, int) or i < 1 or i > len(blocks):
            continue
        seen.add(i)
        block = blocks[i - 1]
        test(f'quote-{i}-context', q.get('context_verified') is True)
        valid_page = isinstance(page, int) and 1 <= page <= len(pages)
        test(f'quote-{i}-page', valid_page)
        test(f'quote-{i}-in-source', valid_page and bool(quote) and normalized(quote) in normalized(pages[page - 1]))
        test(f'quote-{i}-in-note', quote in block and f'**原文引用 {i}**' in block)
        test(f'quote-{i}-page-link', f'?page={page}' in block if zotero_mode else f'PDF第{page}页' in block)
    for link in re.findall(r'\[\[([^\]]+)\]\]', body):
        name = link.replace('\\|', '|').split('|', 1)[0].split('#', 1)[0]
        target = vault / (name if name.endswith('.md') else name + '.md')
        test('related-link-exists', target.is_file())
        if target.is_file():
            try:
                linked, _ = note_fields(target)
                test('related-is-note', linked.get('type') == 'literature-note' or 'literature-note' in linked.get('tags', []))
            except (ValueError, yaml.YAMLError):
                test('related-is-note', False)
    archive = f.get('fulltext_path')
    if archive:
        archive_path = vault / archive
        test('declared-optional-archive-exists', archive_path.is_file())
        if archive_path.is_file():
            try:
                af, _ = note_fields(archive_path)
                test('optional-archive-identity', all(af.get(k) == f.get(k) for k in ['zotero_key', 'pdf_key', 'note_path'] if f.get(k)))
            except (ValueError, yaml.YAMLError):
                test('optional-archive-metadata', False)
    k = review.get('knowledge_decision', {})
    test('knowledge-decision', k.get('action') in {'NO_KNOWLEDGE_CHANGE', 'KNOWLEDGE_UPDATED'} and bool(k.get('reason')))
    if k.get('action') == 'KNOWLEDGE_UPDATED':
        paths = k.get('validation_reports', [])
        valid = bool(paths)
        for path in paths:
            try:
                kr = read_json(path)
                valid &= kr.get('passed') is True and bool(kr.get('checks')) and not kr.get('errors')
            except (OSError, ValueError):
                valid = False
        test('knowledge-validation-reports', valid)
    return {'passed': not errors, 'errors': errors, 'checks': checks, 'note_path': relative, 'source_sha256': actual_hash, 'zotero_key': f.get('zotero_key'), 'knowledge_action': k.get('action'), 'scope': 'Local identity, PDF hash, template, literal quotation and review-record checks. Context/figures/knowledge semantics still require actual agent review.'}


def last_records(path):
    out = {}
    if not Path(path).is_file():
        return out
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get('zotero_key'):
            out[row['zotero_key']] = row
    return out


def summarize(snapshot, c):
    latest, rows = last_records(c['process_log']), []
    current_notes = existing_notes(c['vault_root'])
    counts = {'total': len(snapshot['materials']), 'verified_complete': 0, 'pdf_available': 0, 'note_only': 0, 'unresolved': 0}
    for m in snapshot['materials']:
        key = m['zotero_key']
        row = {'zotero_key': key, 'title': m['item']['data']['title'], 'state': 'PARTIAL_NOTE_MISSING'}
        present = [p for p in m['pdfs'] if p.get('pdf_path') and Path(p['pdf_path']).is_file()]
        available = False
        for p in present:
            try:
                available |= bool(PdfReader(p['pdf_path']).pages)
            except Exception:
                pass
        counts['pdf_available'] += int(available)
        if len(current_notes.get(key, [])) > 1:
            row['state'] = 'KEY_CONFLICT'
        elif not present:
            row['state'] = 'PDF_NOT_FOUND'
        elif not available:
            row['state'] = 'PDF_UNREADABLE'
        record = latest.get(key)
        if record:
            row['last_recorded_state'] = record.get('state')
            row['last_reason'] = record.get('reason', '')
        if record and record.get('state') in TERMINAL and available:
            try:
                result = validate_note(c['vault_root'] / record['note_path'], c['vault_root'], read_json(record['review_path']), m)
                if result['passed']:
                    row.update(state='ALREADY_COMPLETE', note_path=record['note_path'])
                    counts['verified_complete'] += 1
                else:
                    row.update(state='VALIDATION_FAILED', errors=result['errors'])
            except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
                row.update(state='VALIDATION_FAILED', reason=str(exc))
        if row['state'] not in TERMINAL:
            counts['unresolved'] += 1
            counts['note_only'] += int(bool(current_notes.get(key)))
        rows.append(row)
    return {'counts': counts, 'records': rows, 'scope': 'Selected collection snapshot; existing successes revalidated, no automatic notes/Knowledge edits.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    material = sub.add_parser('material')
    select = material.add_mutually_exclusive_group(required=True)
    for arg in ['key', 'title', 'collection', 'collection-name']:
        select.add_argument('--' + arg)
    material.add_argument('--include-subcollections', action='store_true')
    material.add_argument('--out', required=True)
    extract = sub.add_parser('extract')
    extract.add_argument('--material', required=True)
    extract.add_argument('--pdf-key')
    extract.add_argument('--pages', help='Comma-separated physical PDF pages to render')
    extract.add_argument('--out', required=True)
    validate = sub.add_parser('validate')
    validate.add_argument('--note', required=True)
    validate.add_argument('--review', required=True)
    validate.add_argument('--material')
    validate.add_argument('--report', required=True)
    summary = sub.add_parser('summary')
    summary.add_argument('--snapshot', required=True)
    summary.add_argument('--out', required=True)
    record = sub.add_parser('record')
    record.add_argument('--entry', required=True)
    args = parser.parse_args(argv)
    c = config(args.config)
    if args.command == 'material':
        api = Zotero(c['zotero_api_base'])
        items, collection_keys = select_items(api, args)
        notes = existing_notes(c['vault_root'])
        # Abort on an API failure rather than silently omit an in-scope paper.
        materials = [material_for(api, item, c, notes) for item in items]
        for m in materials:
            per_item = Path(args.out).resolve().parent / 'materials' / (m['zotero_key'] + '.json')
            m['material_path'] = str(per_item)
            write_json(per_item, m)
        write_json(args.out, {'schema_version': 1, 'collection_keys': collection_keys, 'materials': materials})
        print(json.dumps({'papers': len(materials), 'output': args.out}))
    elif args.command == 'extract':
        m = read_json(args.material)
        candidates = [p for p in m['pdfs'] if not args.pdf_key or p['pdf_key'] == args.pdf_key]
        if len(candidates) != 1:
            raise ValueError('Select a single PDF attachment explicitly')
        p = candidates[0]
        if digest(p['pdf_path']) != p['source_sha256']:
            raise ValueError('Source changed since material snapshot')
        pages = [pg.extract_text() or '' for pg in PdfReader(p['pdf_path']).pages]
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        write_json(out / 'pages.json', {'source_sha256': p['source_sha256'], 'pages': pages})
        (out / 'pages.txt').write_text('\n\n'.join(f'=== PDF PAGE {i+1} ===\n{t}' for i, t in enumerate(pages)), encoding='utf-8')
        if args.pages:
            import pymupdf
            with pymupdf.open(p['pdf_path']) as document:
                for n in [int(x) for x in args.pages.split(',')]:
                    if not 1 <= n <= len(document):
                        raise ValueError('Render page outside PDF')
                    document[n-1].get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(out / f'page-{n:02d}.png')
        print(json.dumps({'pages': len(pages), 'output': str(out)}))
    elif args.command == 'validate':
        report = validate_note(args.note, c['vault_root'], read_json(args.review), read_json(args.material) if args.material else None)
        write_json(args.report, report)
        print(json.dumps({'passed': report['passed'], 'checks': len(report['checks']), 'errors': report['errors']}, ensure_ascii=False))
        return 0 if report['passed'] else 1
    elif args.command == 'summary':
        result = summarize(read_json(args.snapshot), c)
        write_json(args.out, result)
        print(json.dumps(result['counts']))
    elif args.command == 'record':
        entry = read_json(args.entry)
        if entry.get('state') not in STATES or not KEY_RE.fullmatch(entry.get('zotero_key', '')):
            raise ValueError('Record requires a valid parent key and workflow state')
        if not entry.get('reason'):
            raise ValueError('Record a result reason')
        if entry['state'] in TERMINAL:
            entry['material_path'] = str(Path(entry['material_path']).resolve())
            entry['review_path'] = str(Path(entry['review_path']).resolve())
            m = read_json(entry['material_path'])
            report = validate_note(c['vault_root'] / entry['note_path'], c['vault_root'], read_json(entry['review_path']), m)
            if not report['passed']:
                raise ValueError('Cannot record success: ' + ', '.join(report['errors']))
            if m['zotero_key'] != entry['zotero_key']:
                raise ValueError('Record parent key does not match material')
            entry['source_sha256'] = report['source_sha256']
            entry['knowledge_action'] = report['knowledge_action']
        entry['time'] = dt.datetime.now().astimezone().isoformat()
        c['process_log'].parent.mkdir(parents=True, exist_ok=True)
        with c['process_log'].open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(json.dumps({'recorded': entry['state'], 'zotero_key': entry['zotero_key']}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, yaml.YAMLError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        raise SystemExit(1)
