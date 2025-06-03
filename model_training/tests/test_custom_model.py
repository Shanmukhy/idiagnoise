import unittest
import tensorflow as tf
from unittest.mock import patch, MagicMock, Mock
from model.custom_model import Model  
from tensorflow.keras.applications import ResNet50

class TestModel(unittest.TestCase):
             
        
    def test_is_model_validated(self):
        model = Model(num_classes=2)
        model.final_val_accuracy = 0.7

        # Test when accuracy is less than final_val_accuracy
        self.assertTrue(model.is_model_validated(accuracy=0.6))

        # Test when accuracy is equal to final_val_accuracy
        self.assertFalse(model.is_model_validated(accuracy=0.7))

    def test_custom_enb7(self):
        # Simple test to check if the custom_enb7 method runs without errors
        model = Model(num_classes=15)
        model.custom_enb7(input_shape=(224, 224, 3), num_classes=2)

class TestLoadForTraining(unittest.TestCase):

    def setUp(self):
        self.obj = Model(num_classes=15)
        self.obj.custom_enb7 = Mock(return_value=Mock())
    
    def test_input_shape(self):
        h, w, lr = 224, 224, 0.001
        self.obj.load_fortraining("model", h, w, lr)
        self.assertEqual(self.obj.input_shape, (h, w, 3))

    def test_num_classes(self):
        h, w, lr = 224, 224, 0.001
        self.obj.load_fortraining("model", h, w, lr)
        self.assertEqual(self.obj.num_classes, 15)

if __name__ == '__main__':
    unittest.main()
