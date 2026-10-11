import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import pipeline

class OpenAIMigrationTests(unittest.TestCase):
    def test_extract_traits_uses_openai_output(self):
        with patch.object(pipeline,'openai_generate',return_value='["冷靜", "溫柔"]',create=True):
            self.assertEqual(pipeline.extract_traits('冷靜又溫柔'),['冷靜','溫柔'])

    def test_report_uses_openai_output(self):
        with patch.object(pipeline,'openai_generate',return_value='角色解讀',create=True):
            self.assertEqual(pipeline.generate_final_report('溫柔',['溫柔'],[(0,50,{'name':'角色','moe_traits':['溫柔']})]),'角色解讀')

    def test_responses_request_does_not_store_input(self):
        from unittest.mock import Mock
        client=Mock()
        client.responses.create.return_value=SimpleNamespace(output_text='完成')
        with patch.object(pipeline,'get_client',return_value=client):
            self.assertEqual(pipeline.openai_generate('測試'),'完成')
        request=client.responses.create.call_args.kwargs
        self.assertFalse(request['store'])
        self.assertEqual(request['input'],'測試')

    def test_empty_response_is_actionable(self):
        from unittest.mock import Mock
        client=Mock()
        client.responses.create.return_value=SimpleNamespace(output_text='')
        with patch.object(pipeline,'get_client',return_value=client):
            with self.assertRaisesRegex(RuntimeError,'空白'):
                pipeline.openai_generate('測試')
