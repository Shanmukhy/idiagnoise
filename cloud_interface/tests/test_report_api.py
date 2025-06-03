import unittest
from unittest.mock import Mock
from cloud.report_api import ReportMaintainanceStorage

class TestReportMaintainanceStorage(unittest.TestCase):
    def setUp(self):
        self.storage = ReportMaintainanceStorage()
    
    def test_upload_b64_to_cloud_image(self):
        # Mock the config_instance and BlobServiceClient
        self.storage.config_instance = Mock(dcmimage_container="test_container", blob_endpoint="test_endpoint", account_key="test_key")
        self.storage.BlobServiceClient = Mock()
        self.storage.BlobServiceClient.return_value.get_container_client.return_value.get_blob_client.return_value.exists.return_value = False

        b64_data = "test_base64_data"
        filename = "test_image.png"
        result = self.storage.upload_b64_to_cloud(b64_data, filename, "image")
        self.assertTrue(result)

    def test_upload_b64_to_cloud_report(self):
        # Mock the config_instance and BlobServiceClient
        self.storage.config_instance = Mock(report_container="test_container", blob_endpoint="test_endpoint", account_key="test_key")
        self.storage.BlobServiceClient = Mock()
        self.storage.BlobServiceClient.return_value.get_container_client.return_value.get_blob_client.return_value.exists.return_value = False

        b64_data = "test_base64_data"
        filename = "test_report.txt"
        result = self.storage.upload_b64_to_cloud(b64_data, filename, "report")
        self.assertTrue(result)

    def test_upload_b64_to_cloud_invalid_type(self):
        b64_data = "test_base64_data"
        filename = "test_invalid.txt"
        with self.assertRaises(ValueError):
            self.storage.upload_b64_to_cloud(b64_data, filename, "invalid_type")

if __name__ == '__main__':
    unittest.main()