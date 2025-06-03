import unittest
import tensorflow as tf
from model.test import TestModel

class TestTestModel(unittest.TestCase):
    def setUp(self):
        # Set up any necessary configurations or data for testing
        self.test_model = TestModel()
        self.model_path = r'/home/system/release/idiagnose/inference/tests/saved_model'  
        self.batch_size = 32  

    def test_evaluate_model(self):
        # Test the evaluate method

        # Get the validation dataset
        val_ds = self.test_model.get_val_data(self.batch_size)
        
        # Perform assertions to verify the output
        self.assertIsNotNone(val_ds) 
       
if __name__ == '__main__':
    unittest.main()
