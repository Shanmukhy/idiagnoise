import unittest
import numpy as np
import base64
from model.prepost import PrePost  

class TestPrePost(unittest.TestCase):
    def setUp(self):
        # Set up any necessary configurations or data for testing
        self.pre_post = PrePost()
    
    def test_get_argmax_res(self):
        # Test get_argmax_res method
        
        # Mock input data (prediction result dictionary)
        result = {"prediction": np.array([[0.1, 0.9, 0.2]])}

        # Call the get_argmax_res method
        argmax_res = self.pre_post.get_argmax_res(result)

        # Perform assertions to verify the output
        self.assertEqual(argmax_res, 1)  # Check if the argmax result matches the expected output

if __name__ == "__main__":
    unittest.main()
