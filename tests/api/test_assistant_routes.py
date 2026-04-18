from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from config.settings import Settings
from sepa.api.factory import create_app


class AssistantRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(Settings(enable_docs=False)))

    def test_assistant_health_route_returns_payload(self) -> None:
        with patch(
            'sepa.api.routes_public.assistant_health_payload',
            return_value={'provider': 'ollama', 'ready': True, 'provider_health': {'model': 'qwen3.5:4b'}},
        ) as mocked:
            response = self.client.get('/api/assistant/health')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['provider'], 'ollama')
        mocked.assert_called_once()

    def test_assistant_chat_route_returns_payload(self) -> None:
        with patch(
            'sepa.api.routes_public.assistant_chat_payload',
            return_value={'provider': 'ollama', 'model': 'qwen3.5:4b', 'content': 'hello', 'page_id': 'workspace-home'},
        ) as mocked:
            response = self.client.post(
                '/api/assistant/chat',
                json={
                    'page_id': 'workspace-home',
                    'messages': [{'role': 'user', 'content': '안녕'}],
                    'context': {'page': 'workspace'},
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['content'], 'hello')
        mocked.assert_called_once()


if __name__ == '__main__':
    unittest.main()
