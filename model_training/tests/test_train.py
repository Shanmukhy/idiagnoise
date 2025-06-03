import unittest
from unittest.mock import patch
from argparse import Namespace
from train import parse_args

class TestScript(unittest.TestCase):

    @patch('argparse.ArgumentParser.parse_args', return_value=Namespace(img_height=224, img_width=224, batch_size=32, epochs=1,
                                                                        model="custom", transfer_learning_model_id=None,
                                                                        learning_rate=0.001, csp="azure", train_data_id=None))
    def test_parse_args_default_values(self, mock_args):
        args = parse_args()
        self.assertEqual(args.img_height, 224)
        self.assertEqual(args.img_width, 224)
        self.assertEqual(args.batch_size, 32)
        self.assertEqual(args.epochs, 1)
        self.assertEqual(args.model, "custom")
        self.assertIsNone(args.transfer_learning_model_id)
        self.assertEqual(args.learning_rate, 0.001)
        self.assertEqual(args.csp, "azure")
        self.assertIsNone(args.train_data_id)

    @patch('argparse.ArgumentParser.parse_args', return_value=Namespace(img_height=300, img_width=300, batch_size=64, epochs=5,
                                                                        model="resnet50", transfer_learning_model_id="123",
                                                                        learning_rate=0.01, csp="aws", train_data_id="456"))
    def test_parse_args_custom_values(self, mock_args):
        args = parse_args()
        self.assertEqual(args.img_height, 300)
        self.assertEqual(args.img_width, 300)
        self.assertEqual(args.batch_size, 64)
        self.assertEqual(args.epochs, 5)
        self.assertEqual(args.model, "resnet50")
        self.assertEqual(args.transfer_learning_model_id, "123")
        self.assertEqual(args.learning_rate, 0.01)
        self.assertEqual(args.csp, "aws")
        self.assertEqual(args.train_data_id, "456")

    

    # Add more test cases as needed for different scenarios and edge cases
    

if __name__ == '__main__':
    unittest.main()
