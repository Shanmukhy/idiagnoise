import unittest
from cloud.api import CloudInterface

class TestCloudInterface(unittest.TestCase):
    
    def test_create_SAS_token(self):
        cloud = CloudInterface()
        sas_url = cloud.create_SAS_token("training_data_blob", "idiagnose-train-dataset-container", duration=30)
        self.assertIsNotNone(sas_url)
            
    def test_download_latest(self):
        cloud = CloudInterface()
        latest_url = cloud.download_latest("idiagnose-train-dataset-container")
        self.assertIsNotNone(latest_url)
        
    
        
if __name__ == '__main__':
    unittest.main()