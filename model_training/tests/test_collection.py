import unittest
from unittest.mock import patch
from utils.collection import ModelCollection

class TestModelCollection(unittest.TestCase):

    def setUp(self):
        self.mongo_server = {
            "mongo_uri": "mongodb://localhost:27017/",
            "database_name": "local"
        }
        self.model_collection = ModelCollection(self.mongo_server)

    def test_init(self):
        self.assertEqual(self.model_collection.mongo_uri, self.mongo_server["mongo_uri"])
        self.assertEqual(self.model_collection.database_name, self.mongo_server["database_name"])

    @patch('utils.collection.generate_blob_sas')
    def test_create_SAS_token(self, mock_generate_blob_sas):
        mock_generate_blob_sas.return_value = "mock_sas_token"
        blob_name = "mock_blob_name"
        sas_token = self.model_collection.create_SAS_token(blob_name, duration=30)
        self.assertEqual(sas_token, "https://idiagnoseframeworkdev.blob.core.windows.net/idiagnose-model-container/mock_blob_name?mock_sas_token")


    @patch('utils.collection.MongoClient')
    @patch('utils.collection.ZipFile')
    @patch('utils.collection.wget')
    def test_download_model(self, mock_wget, mock_zipfile, mock_mongo_client):
        mock_blob_info = {
            "version_id": "mock_version_id",
            "backbone": "mock_backbone_name",
            "model_name": "mock_model_name"
        }
        mock_mongo_collection = mock_mongo_client.return_value.__getitem__.return_value
        mock_mongo_collection.find_one.return_value = mock_blob_info
        model_path = None
        downloaded_path = self.model_collection.download_model(model_path, "mock_backbone_name", "mock_version_id")
        self.assertEqual(downloaded_path, model_path)




if __name__ == '__main__':
    unittest.main()