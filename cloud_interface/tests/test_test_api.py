import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContainerClient, ContentSettings
from cloud.test_api import TestDataStorage

class TestTestDataStorage(unittest.TestCase):

    @patch('azure.storage.blob.ContainerClient.upload_blob')
    @patch('azure.storage.blob.ContainerClient.get_blob_client')
    def test_upload_blob_success(self, mock_get_blob_client, mock_upload_blob):
        # Arrange
        config_instance = MagicMock()
        config_instance.blob_endpoint = "https://idiagnoseframeworkdev.blob.core.windows.net/"
        config_instance.account_key = "qadJyMkmlddPHUrIQF7pStHhSIOjULCiWbCETd2Y15Kthu5ws0CuGMSwMkWo6mEYs/HyvNEIMylh+AStRkk5Mg=="
        mock_blob_service_client = MagicMock()
        mock_blob_service_client.get_container_client.return_value = MagicMock()
        mock_get_blob_client.return_value = MagicMock()
        mock_upload_blob.return_value = MagicMock(url="https://training_data_blob.core.windows.net/idiagnose-train-dataset-container/training_data_blob.zip")
        with patch('azure.storage.blob.BlobServiceClient', return_value=mock_blob_service_client):
            data_storage = TestDataStorage()

            # Act
            result = data_storage.upload_blob("idiagnose-train-dataset-container", "training_data_blob.zip", b"mock_data")

            # Assert
            self.assertTrue(result.startswith(config_instance.blob_endpoint))
            self.assertTrue(result.endswith("idiagnose-train-dataset-container/training_data_blob.zip"))
            mock_upload_blob.assert_called_once_with(name="training_data_blob.zip", data=b"mock_data", content_settings=ContentSettings(content_type='application/zip'))

    @patch('azure.storage.blob.ContainerClient.upload_blob', side_effect=Exception('Upload Error'))
    def test_upload_blob_upload_error(self, mock_upload_blob):
        # Arrange
        config_instance = MagicMock()
        config_instance.blob_endpoint = "https://idiagnoseframeworkdev.blob.core.windows.net/"
        config_instance.account_key = "qadJyMkmlddPHUrIQF7pStHhSIOjULCiWbCETd2Y15Kthu5ws0CuGMSwMkWo6mEYs/HyvNEIMylh+AStRkk5Mg=="
        mock_blob_service_client = MagicMock()
        mock_blob_service_client.get_container_client.return_value = MagicMock()
        mock_upload_blob.side_effect = Exception('Upload Error')
        with patch('azure.storage.blob.BlobServiceClient', return_value=mock_blob_service_client):
            data_storage = TestDataStorage()

            # Act / Assert
            with self.assertRaises(Exception):
                data_storage.upload_blob("idiagnose-train-dataset-container", "training_data_blob.zip", b"mock_data")

    def test_generate_name(self):
        # Arrange
        data_storage = TestDataStorage()

        # Act
        result = data_storage.generate_name()

        # Assert
        self.assertTrue(result[0].startswith('test_data_'))
        self.assertTrue(result[0].endswith('.zip'))
        self.assertTrue(result[1].startswith('test_data_'))
        self.assertEqual(len(result[1]), 24)  # Length of timestamp string (YYYYMMDDHHMMSS)
        self.assertIsInstance(result[2], str)
        self.assertEqual(len(result[2]), 14)  # Length of timestamp string (YYYYMMDDHHMMSS)

if __name__ == '__main__':
    unittest.main()
