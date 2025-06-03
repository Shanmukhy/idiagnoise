import unittest
import tensorflow as tf
from tensorflow.keras.utils import to_categorical
from tensorflow.data import Dataset
from model.rapid_model import RapidModel

class TestRapidModel(unittest.TestCase):

    def setUp(self):
        self.num_classes = 15  
        self.img_height = 224
        self.img_width = 224
        self.lr = 0.001
        self.epochs = 2

        # Dummy data for testing
        self.dummy_train_ds = Dataset.from_tensor_slices(
            (tf.random.normal((100, self.img_height, self.img_width, 3)),
             to_categorical(tf.random.uniform((100,), maxval=self.num_classes), num_classes=self.num_classes))
        ).batch(32)

        self.dummy_val_ds = Dataset.from_tensor_slices(
            (tf.random.normal((20, self.img_height, self.img_width, 3)),
             to_categorical(tf.random.uniform((20,), maxval=self.num_classes), num_classes=self.num_classes))
        ).batch(32)

    def test_load_fortraining_valid_model(self):
        rapid_model = RapidModel(self.num_classes)
        rapid_model.load_fortraining('resnet50', self.img_height, self.img_width, self.lr)
        self.assertIsInstance(rapid_model.model, tf.keras.Sequential)

    def test_load_fortraining_invalid_model(self):
        rapid_model = RapidModel(self.num_classes)
        with self.assertRaises(ValueError):
            rapid_model.load_fortraining('invalid_model', self.img_height, self.img_width, self.lr)


  

if __name__ == '__main__':
    unittest.main()
