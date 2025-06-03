import unittest
import tensorflow as tf
from model.compile import TFTRTCompile  

class TestTFTRTCompile(unittest.TestCase):
    def setUp(self):
        # Set up any necessary configurations or data for testing
        self.model_path = "saved_model"
        self.test_data_folder = r"/inference/tests/test_data"  
        self.val_ds = self.create_test_dataset()

    def create_test_dataset(self):
        # Create a test dataset from the images in the specified folder
        test_dataset = tf.keras.preprocessing.image_dataset_from_directory(
            self.test_data_folder,
            image_size=(224, 224),
            batch_size=32,
            shuffle=False,
        )
        return test_dataset

    def test_compile_fp32(self):
        # Test case for FP32 precision mode
        compiler = TFTRTCompile(self.model_path, "fp32")
        compiler.build(self.val_ds)
        compiler.compile()
        save_path = r"/inference/tests/saved_model"  # Replace with the desired save path
        compiler.save(save_path)

    def test_compile_fp16(self):
        # Test case for FP16 precision mode
        compiler = TFTRTCompile(self.model_path, "fp16")
        compiler.build(self.val_ds)
        compiler.compile()
        save_path = r"/inference/tests/saved_model"  # Replace with the desired save path
        compiler.save(save_path)

    def test_compile_int8(self):
        # Test case for INT8 precision mode
        compiler = TFTRTCompile(self.model_path, "int8")
        compiler.build(self.val_ds)
        compiler.compile()
        save_path = r"/inference/tests/saved_model"  # Replace with the desired save path
        compiler.save(save_path)

    def tearDown(self):
        # Clean up any resources if needed
        pass

if __name__ == "__main__":
    unittest.main()
