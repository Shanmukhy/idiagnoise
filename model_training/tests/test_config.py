import unittest
from unittest.mock import mock_open, patch
from utils.config import Config

class TestConfig(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data='{"account_name": "idiagnoseframeworkdev"}') 
    def test_load_config_success(self, mock_file):
        config = Config("config/config.json")
        result = config.load_config()
        self.assertEqual(result, {"account_name": "idiagnoseframeworkdev"})
      
    @patch('builtins.open', new_callable=mock_open, read_data='{"model": {"img_height": 224, "img_width": 224, "batch_size": 32, "epochs": 10, "learning_rate": 0.001}}')
    def test_set_model_config_success(self, mock_file):
        config = Config("config/config.json")
        args = type('Namespace', (object,), {})
        args.model = "model"
        args.img_height = None
        args.img_width = None
        args.batch_size = None
        args.epochs = None
        args.learning_rate = None

        data = config.load_config()
        result = config.set_model_config(data, args)

        self.assertEqual(result.img_height, 224)
        self.assertEqual(result.img_width, 224)
        self.assertEqual(result.batch_size, 32)
        self.assertEqual(result.epochs, 10)
        self.assertEqual(result.learning_rate, 0.001)

if __name__ == '__main__':
    unittest.main()
