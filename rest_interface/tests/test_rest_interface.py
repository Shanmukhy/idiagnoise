import unittest
import tempfile
import os
from flask import Flask
from flask.testing import FlaskClient
from rest_interface import app ,infer_lungs
from unittest.mock import patch


class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.add_url_rule('/api/infer/lungs-xray', 'infer_lungs', infer_lungs, methods=['POST'])
        self.client = self.app.test_client()
        
    def test_valid_input_supported_image_type(self):
        response = self.client.post('/api/infer/lungs-xray', json={"fromSearch": False, "file": "test.jpg", "img_type": "jpg"})
        self.assertEqual(response.status_code, 500)

    def test_valid_input_unsupported_image_type(self):
        response = self.client.post('/api/infer/lungs-xray', json={"fromSearch": False, "file": "test.jpg", "img_type": "gif"})
        self.assertEqual(response.status_code, 500)

    def test_invalid_input_data(self):
        response = self.client.post('/api/infer/lungs-xray', json={"fromSearch": True, "file": "test.jpg", "img_type": "jpg"})
        self.assertEqual(response.status_code, 500)

    def test_request_method_other_than_post(self):
        response = self.client.get('/api/infer/lungs-xray')
        self.assertEqual(response.status_code, 500)

    def test_invalid_input_data(self):
        response = self.client.post('/api/infer/lungs-xray', json={"fromSearch": True, "file": "test.jpg", "img_type": "jpg"})
        self.assertEqual(response.status_code, 500)

    def test_request_method_other_than_post(self):
        response = self.client.get('/api/infer/lungs-xray')
        self.assertEqual(response.status_code, 405)

    def test_test_lungs(self):
        response = self.client.post('/api/test/lungs-xray', json={})
        self.assertEqual(response.status_code, 404)

    def test_feedback_lungs(self):
        response = self.client.post('/api/ai-feedback/lungs-xray', json={})
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
