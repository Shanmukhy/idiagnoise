import unittest
from unittest.mock import patch, MagicMock
from utils.dataprocessing import Dataset
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator

class TestDataset(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Set up any common data needed for the tests
        self.data_dir = 'tests/test_data'
        self.img_h = 224
        self.img_w = 224
        self.mongo_server = {
            'mongo_uri': 'mongodb://localhost:27017/',
            'database_name': 'test_db'
        }
        self.dataset = Dataset(self.data_dir, self.img_h, self.img_w, self.mongo_server)

    @patch('tensorflow.keras.preprocessing.image.ImageDataGenerator.flow_from_directory')
    def test_get_augmented_train_data(self, mock_flow_from_directory):
        dataset = Dataset(self.data_dir, self.img_h, self.img_w, self.mongo_server)

        # Set up mock objects
        mock_generator = MagicMock()
        mock_flow_from_directory.return_value = mock_generator

        # Call the method
        result = dataset.get_augmented_train_data(batch_size=32)

        # Check if the method is called correctly
        mock_flow_from_directory.assert_called_once_with(
            self.data_dir,
            subset="training",
            seed=123,
            target_size=(self.img_h, self.img_w),
            batch_size=32,
            class_mode='categorical'
        )

        # Check the result
        self.assertEqual(result, mock_generator)

    @patch('tensorflow.keras.preprocessing.image.ImageDataGenerator.flow_from_directory')
    def test_get_augmented_val_data(self, mock_flow_from_directory):
        dataset = Dataset(self.data_dir, self.img_h, self.img_w, self.mongo_server)

        # Set up mock objects
        mock_generator = MagicMock()
        mock_flow_from_directory.return_value = mock_generator

        # Call the method
        result = dataset.get_augmented_val_data(batch_size=32)

        # Check if the method is called correctly
        mock_flow_from_directory.assert_called_once_with(
            self.data_dir,
            subset="validation",
            seed=123,
            target_size=(self.img_h, self.img_w),
            batch_size=32,
            class_mode='categorical'
        )

        # Check the result
        self.assertEqual(result, mock_generator)

    
    def test_histogram_stretching(self):
        image = np.random.rand(224, 224, 3)
        result = self.dataset.histogram_stretching(image)
        self.assertEqual(result.shape, (224, 224, 3))

    
    def test_get_augment_generator(self):
        result = self.dataset.get_augment_generator()
        self.assertIsInstance(result, ImageDataGenerator)


if __name__ == '__main__':
    unittest.main()
