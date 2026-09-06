from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch

class VerificationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.verify_url = '/api/verify/'

    @patch('verification.engine.VerificationEngine')
    def test_verify_endpoint(self, MockEngine):
        # Setup mock return value
        mock_instance = MockEngine.return_value
        mock_instance.verify.return_value = {
            "query": "Is aspirin safe?",
            "raw_response": "Aspirin is safe.",
            "claims": [
                {
                    "text": "Aspirin is safe.",
                    "status": "VERIFIED",
                    "confidence": 0.95,
                    "evidence": []
                }
            ],
            "trust_score": 100.0
        }

        # Mock get_engine to return our mock instance
        with patch('verification.views.get_engine', return_value=mock_instance):
            data = {
                "query": "Is aspirin safe?",
                "response_text": "Aspirin is safe."
            }
            response = self.client.post(self.verify_url, data, format='json')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['trust_score'], 100.0)
            self.assertEqual(len(response.data['claims']), 1)
            self.assertEqual(response.data['claims'][0]['status'], 'VERIFIED')

    def test_missing_response_text(self):
        data = {"query": "Test"}
        response = self.client.post(self.verify_url, data, format='json')
        self.assertEqual(response.status_code, 400)
