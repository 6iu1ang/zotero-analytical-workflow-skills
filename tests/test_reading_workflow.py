import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/research-vault-ingest-orchestrator/scripts/reading_workflow.py'
spec = importlib.util.spec_from_file_location('reading_workflow', SCRIPT)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def make_pdf(path):
    writer = PdfWriter()
    for sentence in ['The reservoir reduced sediment transport.', 'No reduction occurred under extreme flooding.']:
        page = writer.add_blank_page(width=400, height=300)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        content = DecodedStreamObject()
        content.set_data(f'BT /F1 12 Tf 20 200 Td ({sentence}) Tj ET'.encode('ascii'))
        page[NameObject('/Contents')] = writer._add_object(content)
    writer.write(path)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.vault = self.root / 'vault'
        self.vault.mkdir()
        self.source = self.root / 'source.pdf'
        make_pdf(self.source)
        self.note = self.vault / 'note.md'
        self.key, self.pdfkey = 'ABCDEFGH', 'HGFEDCBA'
        self.f = {k: 'confirmed' for k in w.NOTE_FIELDS}
        self.f.update(title='Example sediment study', aliases=[], tags=['literature-note'], author=['Example Author'], year=2026, source_type='zotero_pdf', source_file=self.source.as_posix(), source_sha256=w.digest(self.source), note_path='note.md', zotero_key=self.key, pdf_key=self.pdfkey, doi='10.example/test')
        sections = []
        for heading in w.HEADINGS:
            contents = 'Confirmed source and analysis.'
            if heading == '研究方法':
                contents = '### 方法概述\n\nObservation.\n\n### 方法分析\n\nCompare periods.'
            if heading == '基本信息':
                contents = f'[条目](zotero://select/library/items/{self.key}) [PDF](zotero://open-pdf/library/items/{self.pdfkey})'
            if heading == '研究结论':
                contents = f'- **主要发现 1**：限定条件下输沙减少。\n- **原文引用 1**：[PDF第1页](zotero://open-pdf/library/items/{self.pdfkey}?page=1)。\n\n> The reservoir reduced sediment transport.'
            sections.append(f'## {heading}\n\n{contents}')
        self.body = '\n\n'.join(sections) + '\n'
        self.write_note()
        self.review = {'source_sha256': self.f['source_sha256'], 'context_verified': True, 'quotes': [{'finding_number': 1, 'page': 1, 'quote': 'The reservoir reduced sediment transport.', 'context_verified': True}], 'formulas': {'applicable': False}, 'figures': {'applicable': False}, 'knowledge_decision': {'action': 'NO_KNOWLEDGE_CHANGE', 'reason': 'No cross-paper claim assembled.'}}
        self.material = {'zotero_key': self.key, 'item': {'key': self.key, 'data': {'title': self.f['title'], 'DOI': self.f['doi']}}, 'pdfs': [{'pdf_key': self.pdfkey, 'pdf_path': str(self.source), 'source_sha256': self.f['source_sha256'], 'exists': True, 'readable': True}], 'existing_notes': ['note.md']}
        self.reviewpath = self.root / 'review.json'
        w.write_json(self.reviewpath, self.review)
        self.config = {'vault_root': self.vault, 'process_log': self.root / 'process.jsonl'}

    def tearDown(self):
        self.temp.cleanup()

    def write_note(self):
        self.note.write_text('---\n' + yaml.safe_dump(self.f, allow_unicode=True) + '---\n\n' + self.body, encoding='utf-8')

    def validate(self):
        return w.validate_note(self.note, self.vault, self.review, self.material)

    def success_log(self):
        row = {'zotero_key': self.key, 'state': 'COMPLETE', 'note_path': 'note.md', 'review_path': str(self.reviewpath), 'reason': 'Reviewed.'}
        self.config['process_log'].write_text(json.dumps(row) + '\n', encoding='utf-8')

    def test_valid_without_fulltext_archive(self):
        self.assertTrue(self.validate()['passed'])
        self.assertNotIn('fulltext_path', self.f)

    def test_wrong_physical_page_fails(self):
        self.review['quotes'][0]['page'] = 2
        result = self.validate()
        self.assertFalse(result['passed'])
        self.assertIn('quote-1-in-source', result['errors'])

    def test_negation_cannot_be_removed_from_quote(self):
        self.review['quotes'][0]['page'] = 2
        self.review['quotes'][0]['quote'] = 'reduction occurred under extreme flooding.'
        # Literal substring checks alone cannot certify context. Explicit review is required.
        self.review['quotes'][0]['context_verified'] = False
        self.assertIn('quote-1-context', self.validate()['errors'])

    def test_changed_source_hash_fails(self):
        with self.source.open('ab') as stream:
            stream.write(b'\n% changed version\n')
        self.assertIn('source-hash', self.validate()['errors'])

    def test_missing_pdf_fails(self):
        self.source.unlink()
        self.assertIn('source-exists', self.validate()['errors'])

    def test_pdf_attachment_identity_fails(self):
        self.material['pdfs'][0]['pdf_key'] = 'ZZZZZZZZ'
        self.assertIn('material-attachment-source', self.validate()['errors'])

    def test_duplicate_parent_note_fails(self):
        (self.vault / 'duplicate.md').write_text(self.note.read_text(encoding='utf-8'), encoding='utf-8')
        self.assertIn('parent-unique-in-vault', self.validate()['errors'])

    def test_declared_broken_archive_fails(self):
        self.f['fulltext_path'] = 'missing.md'
        self.write_note()
        self.assertIn('declared-optional-archive-exists', self.validate()['errors'])

    def test_formula_review_cannot_be_assumed(self):
        self.review['formulas'] = {'applicable': True, 'verified': False, 'pages': [1]}
        self.assertIn('formulas-review', self.validate()['errors'])

    def test_existing_complete_is_revalidated(self):
        self.success_log()
        self.assertEqual(w.summarize({'materials': [self.material]}, self.config)['records'][0]['state'], 'ALREADY_COMPLETE')
        self.note.write_text(self.note.read_text(encoding='utf-8').replace('The reservoir reduced sediment transport.', 'A fabricated finding.'), encoding='utf-8')
        result = w.summarize({'materials': [self.material]}, self.config)
        self.assertEqual(result['records'][0]['state'], 'VALIDATION_FAILED')
        self.assertEqual(result['counts']['verified_complete'], 0)

    def test_old_success_with_missing_pdf_is_not_skipped(self):
        self.success_log()
        self.source.unlink()
        result = w.summarize({'materials': [self.material]}, self.config)
        self.assertEqual(result['records'][0]['state'], 'PDF_NOT_FOUND')
        self.assertEqual(result['counts']['pdf_available'], 0)

    def test_api_pagination(self):
        class Fake(w.Zotero):
            def __init__(self):
                self.calls = []
            def get(self, route):
                self.calls.append(route)
                start = int(route.split('start=')[1])
                return list(range(start, min(start + 100, 205)))
        api = Fake()
        self.assertEqual(len(api.all('collections/ABCDEFGH/items/top')), 205)
        self.assertEqual(len(api.calls), 3)

    def test_quote_normalization_handles_wrapped_compounds(self):
        self.assertEqual(w.normalized('climate-\ndriven sediment'), w.normalized('climate-driven sediment'))
        self.assertNotEqual(w.normalized('−1.08'), w.normalized('1.08'))

    def test_attachment_path_blocks_traversal(self):
        item = {'key': self.pdfkey, 'data': {'filename': '../private.pdf', 'linkMode': 'imported_file'}}
        self.assertIsNone(w.attachment_path(self.root, item))

    def test_config_paths_are_relative_to_config(self):
        (self.root / 'zotero').mkdir()
        p = self.root / 'config.json'
        w.write_json(p, {'vault_root': 'vault', 'zotero_data_dir': 'zotero', 'work_dir': 'work', 'process_log': 'work/log.jsonl'})
        self.assertEqual(w.config(p)['vault_root'], self.vault.resolve())

    def test_pdf_only_does_not_require_zotero_identity(self):
        self.f.update(source_type='user_pdf')
        self.f.pop('zotero_key')
        self.f.pop('pdf_key')
        self.body = self.body.replace(f'[PDF](zotero://open-pdf/library/items/{self.pdfkey})', f'[PDF]({self.source.as_posix()})')
        self.write_note()
        result = w.validate_note(self.note, self.vault, self.review)
        self.assertTrue(result['passed'], result['errors'])


if __name__ == '__main__':
    unittest.main()
