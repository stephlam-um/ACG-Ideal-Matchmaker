import unittest
from unittest.mock import patch
from pathlib import Path
from streamlit.testing.v1 import AppTest

class InterfaceTests(unittest.TestCase):
    def test_catalog_opens_without_api_key(self):
        with patch('pipeline.get_api_key', return_value=None):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=20)
        self.assertEqual(len(app.exception), 0)
        self.assertIn('先認識幾位角色', [heading.value for heading in app.subheader])

    def test_empty_submission_shows_guidance(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=20)
        app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn('先寫下你喜歡的性格或相處方式。', [warning.value for warning in app.warning])
