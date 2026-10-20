import importlib.util
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pandas as pd

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('library_index', SCRIPTS / 'create-library-index.py')
index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(index)


class FreeDownloadTests(unittest.TestCase):
    def test_local_file_url_fallback_and_missing_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            previous_docs = index.docs
            index.docs = replace(index.docs, dest_path=Path(directory))
            self.addCleanup(setattr, index, 'docs', previous_docs)
            Path(directory, 'local.pdf').touch()
            rows = [
                ('local', 'local.pdf', 'https://example.org/original.pdf', 'Open'),
                ('remote', 'missing.pdf', 'https://example.org/remote.pdf', 'Open'),
                ('url_only', '', 'https://example.org/url-only.pdf', 'Open'),
                ('missing', 'missing.pdf', '', 'Open'),
                ('blank', '', '   ', 'Open'),
                ('publisher', '', 'https://example.org/publisher.pdf', 'Access via publisher'),
            ]
            data = pd.DataFrame(rows, columns=['ID', 'PDF_file_name', 'Published_URL', 'Access'])
            log = Mock()
            result = index.set_url_and_icon(log, index.replace_openaccess_without_file(log, data))
            result = result.set_index('ID')
            self.assertEqual(result.loc['local', 'URL'], index.urls.download + 'local.pdf')
            for key, url in [('remote', 'remote'), ('url_only', 'url-only')]:
                self.assertEqual(result.loc[key, 'URL'], f'https://example.org/{url}.pdf')
                self.assertEqual(result.loc[key, 'Access'], 'Open')
                self.assertEqual(result.loc[key, 'Icon'], index.icons.download)
            for key in ['missing', 'blank']:
                self.assertEqual(result.loc[key, 'Access'], 'Contact us')
                self.assertEqual(result.loc[key, 'URL'], index.urls.physical_library)
                self.assertEqual(result.loc[key, 'Icon'], index.icons.library)
            self.assertEqual(result.loc['publisher', 'URL'], 'https://example.org/publisher.pdf')
            self.assertEqual(log.warning.call_count, 2)


if __name__ == '__main__':
    unittest.main()
