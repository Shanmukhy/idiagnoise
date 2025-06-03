import unittest
import json
from utils.config import Config  

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Set up any necessary configurations or data for testing
        self.valid_file_path = r'/home/system/release/idiagnose/inference/config/default_model.json'
        

    def test_get_version_id_valid_file(self):
        # Test get_version_id method with a valid file

        # Create a Config instance with a valid file path
        config = Config(self.valid_file_path)

        # Call the get_version_id method
        version_id = config.get_version_id()

        # Perform assertions to verify the output
        self.assertEqual(version_id, 'V20240210110128')  

    

if __name__ == "__main__":
    unittest.main()
