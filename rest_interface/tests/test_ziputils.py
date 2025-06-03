from utils.zip_utils import ZipManager
import unittest
import zipfile
import os
from unittest.mock import Mock

class TestZipManager(unittest.TestCase):
    def setUp(self):
        # Create a sample zip file for testing
        self.sample_zip_path = 'test.zip'
        with zipfile.ZipFile(self.sample_zip_path, 'w') as zipf:
            zipf.writestr('valid.jpg', b'Sample JPEG content')
            zipf.writestr('valid.png', b'Sample PNG content')
            # zipf.writestr('invalid.txt', b'Sample text content')

    def tearDown(self):
        # Clean up after tests
        os.remove(self.sample_zip_path)

    def test_write(self):
        data = Mock()  # Mocking the data object
        zip_manager = ZipManager(data)
        zip_manager.write(self.sample_zip_path)
        self.assertEqual(zip_manager.filename, self.sample_zip_path)

    def test_list_zip_data(self):
        data = Mock()  # Mocking the data object
        zip_manager = ZipManager(data)
        zip_manager.write(self.sample_zip_path)
        file_list = zip_manager.list_zip_data()
        self.assertEqual(file_list, ['valid.jpg', 'valid.png'])

    def test_extract(self):
        data = Mock()  # Mocking the data object
        zip_manager = ZipManager(data)
        zip_manager.write(self.sample_zip_path)
        extract_path = 'extracted'
        zip_manager.extract(extract_path)
        self.assertTrue(os.path.exists(extract_path))
        self.assertTrue(os.path.exists(os.path.join(extract_path, 'valid.jpg')))
        self.assertTrue(os.path.exists(os.path.join(extract_path, 'valid.png')))

    def test_validate_dataset(self):
        # Create a sample directory structure for testing
        os.makedirs('tests/datas/test_dataset')
        os.makedirs(os.path.join('tests/datas/test_dataset', 'class1'))
        with open(os.path.join('tests/datas/test_dataset', 'class1', 'valid.jpg'), 'w') as f:
            f.write('Sample content')
        with open(os.path.join('tests/datas/test_dataset', 'class1', 'invalid.txt'), 'w') as f:
            f.write('Sample content')
        with open(os.path.join('tests/datas/test_dataset', 'class1', 'invalid.png'), 'w') as f:
            f.write('Sample content')  # Creating invalid file format
        
        data = Mock()  # Mocking the data object
        zip_manager = ZipManager(data)
        zip_manager.path = 'tests/datas/test_dataset'
        zip_manager.NUM_CLASSES = 1  # Set a known number of classes
        
        # Test for a valid dataset
        # zip_manager.validate_dataset()  # This should not raise any errors
        
        # Test for an invalid dataset (wrong format)
        with self.assertRaises(ValueError):
            zip_manager.validate_dataset()
        
        # Clean up
        os.remove(os.path.join('tests/datas/test_dataset', 'class1', 'invalid.png'))
        os.remove(os.path.join('tests/datas/test_dataset', 'class1', 'invalid.txt'))
        os.remove(os.path.join('tests/datas/test_dataset', 'class1', 'valid.jpg'))
        os.rmdir(os.path.join('tests/datas/test_dataset', 'class1'))
        os.rmdir('tests/datas/test_dataset')