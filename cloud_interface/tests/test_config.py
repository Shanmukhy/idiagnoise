import unittest
from unittest.mock import patch, mock_open
from utils.config import config

class TestConfig(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data='{"report_blob": {"account_name": "test_account", "account_key": "test_key", "container_name": "test_container", "blob_service_endpoint": "test_endpoint"}, "training_data_blob": {"container_name": "train_container"}, "model_blob": {"container_name": "model_container"}, "dcmimage_blob": {"container_name": "dcmimage_container"}}')
    def test_config_initialization(self, mock_file):
        test_config = config()
        self.assertEqual(test_config.account_name, "test_account")
        self.assertEqual(test_config.account_key, "test_key")
        self.assertEqual(test_config.report_container, "test_container")
        self.assertEqual(test_config.blob_endpoint, "test_endpoint")
        self.assertEqual(test_config.train_container, "train_container")
        self.assertEqual(test_config.model_container, "model_container")
        self.assertEqual(test_config.dcmimage_container, "dcmimage_container")

if __name__ == '__main__':
    unittest.main()