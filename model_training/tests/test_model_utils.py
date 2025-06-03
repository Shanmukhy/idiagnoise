import unittest
from unittest.mock import patch
from datetime import datetime
from model.model_utils import ModelMeta

class TestModelMeta(unittest.TestCase):

    @patch('model.model_utils.datetime')
    def test_generate_model_name(self, mock_datetime):
        # Set a fixed date and time for the test
        mock_datetime.now.return_value = datetime(2024, 2, 14, 15, 35, 47)

        # Create an instance of the ModelMeta class
        model_meta = ModelMeta()

        # Call the method to be tested
        result = model_meta.generate_model_name()

        # Assert the result matches the expected model name
        self.assertEqual(result, "model_14022024_153547")

    @patch('model.model_utils.datetime')
    def test_generate_current_datetime(self, mock_datetime):
        # Set a fixed date and time for the test
        mock_datetime.now.return_value = datetime(2024, 2, 14, 21, 13, 25)

        # Create an instance of the ModelMeta class
        model_meta = ModelMeta()

        # Call the method to be tested
        result = model_meta.generate_current_datetime()

        # Assert the result matches the expected current datetime
        self.assertEqual(result, "14-02-2024 21:13:25")

    @patch('model.model_utils.datetime')
    def test_generate_version_id(self, mock_datetime):
        # Set a fixed date and time for the test
        mock_datetime.now.return_value = datetime(2024, 2, 14, 21, 13, 25)

        # Create an instance of the ModelMeta class
        model_meta = ModelMeta()

        # Call the method to be tested
        result = model_meta.generate_version_id()

        # Assert the result matches the expected version ID
        self.assertEqual(result, "V21132520240214")

if __name__ == '__main__':
    unittest.main()
