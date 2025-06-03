import unittest
import json
import base64
from flask import Flask
from flask.testing import FlaskClient
from inference import app
import argparse

class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def tearDown(self):
        pass

    def image_to_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            binary_data = image_file.read()
            base64_data = base64.b64encode(binary_data).decode("utf-8")
        return base64_data

    def test_infer_xray(self):
        image_path = "inference/tests/test_data/Atelectasis/00000011_006.png"
        base64_image = self.image_to_base64(image_path)
        data = {'patient_dicom': str(base64_image), 'dtype': 'utf-8'}

        response = self.client.post('/api/infer/lungs_xray', json=data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.get_data(as_text=True))
        self.assertIn('ai_result', result)

        

if __name__ == '__main__':
    unittest.main()
