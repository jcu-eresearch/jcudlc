import importlib.util
import sys
import unittest
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import confighelper as cfg
spec = importlib.util.spec_from_file_location('excel_parser', SCRIPTS / 'parse-excel-file.py')
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)


class PlaceholderTests(unittest.TestCase):
    def test_defaults_and_missing_values(self):
        for value in ['NA', 'nan', 'NaN', 'N/A', 'n/a', 'NULL', ' NA ', None, float('nan')]:
            self.assertEqual(parser.normalise_cell(value), '')
        self.assertEqual(parser.normalise_cell(' null '), 'null')

    def test_custom_and_empty_marker_lists(self):
        with patch.object(parser, 'EMPTY_CELL_MARKERS', frozenset(['missing'])):
            self.assertEqual(parser.normalise_cell(' missing '), '')
            self.assertEqual(parser.normalise_cell(' NA '), 'NA')
        with patch.object(parser, 'EMPTY_CELL_MARKERS', frozenset()):
            self.assertEqual(parser.normalise_cell(' NULL '), 'NULL')
            self.assertEqual(parser.normalise_cell(None), '')

    def test_config_validation(self):
        for markers in [None, 'NA', [1]]:
            with self.subTest(markers=markers), self.assertRaisesRegex(ValueError, 'list of strings'):
                cfg.get_sheet_config({**cfg.config, 'excel': {**cfg.config['excel'], 'empty_cell_markers': markers}})
        result = cfg.get_sheet_config({**cfg.config, 'excel': {**cfg.config['excel'], 'empty_cell_markers': []}})
        self.assertEqual(result.empty_cell_markers, frozenset())

    def test_excel_preserves_unconfigured_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'markers.xlsx'
            pd.DataFrame(['NA', 'NULL', 'custom']).to_excel(path, index=False, header=False)
            values = pd.read_excel(path, header=None, dtype='str', keep_default_na=False)[0]
            with patch.object(parser, 'EMPTY_CELL_MARKERS', frozenset(['custom'])):
                self.assertEqual(values.map(parser.normalise_cell).tolist(), ['NA', 'NULL', ''])
