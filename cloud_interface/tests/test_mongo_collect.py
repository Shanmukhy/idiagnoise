import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from pymongo.errors import WriteError, OperationFailure, DuplicateKeyError
from utils.mongo_collect import MongoCollection

class TestMongoCollection(unittest.TestCase):

    @patch('pymongo.collection.Collection.insert_one', return_value=MagicMock(inserted_id='123'))
    def test_train_data_db_update_success(self, mock_insert_one):
        # Arrange
        mongo_instance = MongoCollection()
        train_id = 'train_123'
        blob_url = 'https://training_data_blob.core.windows.net/idiagnose-train-dataset-container/training_data_blob'
        blob_name = 'training_data_blob'
        timestamp = datetime.now()

        # Act
        result = mongo_instance.Train_data_DB_update(train_id, blob_url, blob_name, timestamp)

        # Assert
        mock_insert_one.assert_called_once_with({
            "train_id": train_id,
            "Blob_URL": blob_url,
            "Blob_name": blob_name,
            "timestamp": timestamp
        })
        self.assertEqual(result, '123')
    
    @patch('pymongo.collection.Collection.insert_one', return_value=MagicMock(inserted_id='456'))
    def test_test_data_db_update_success(self, mock_insert_one):
        # Arrange
        mongo_instance = MongoCollection()
        test_id = 'test_456'
        blob_url = 'https://training_data_blob.core.windows.net/idiagnose-train-dataset-container/training_data_blob.zip'
        blob_name = 'training_data_blob.zip'
        timestamp_str = '20220219120000'

        # Act
        result = mongo_instance.Test_data_DB_update(test_id, blob_url, blob_name, timestamp_str)

        # Assert
        mock_insert_one.assert_called_once_with({
            "test_id": test_id,
            "Blob_URL": blob_url,
            "Blob_name": blob_name,
            "timestamp": timestamp_str
        })
        self.assertEqual(result, '456')

        
if __name__ == '__main__':
    unittest.main()
