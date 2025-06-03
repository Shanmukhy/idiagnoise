import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
from zipfile import ZipFile
from tempfile import NamedTemporaryFile
from contextlib import redirect_stdout
from utils.model_utils import ModelChecker  

class TestModelChecker(unittest.TestCase):

    def setUp(self):
        self.model_checker = ModelChecker()

    @patch('utils.model_utils.requests.post')
    def test_check_version_id(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = [{'timestamp': '20220216120000', 'train_id': '1'},
                                                     {'timestamp': '20220216130000', 'train_id': '2'}]

        result = self.model_checker.check_version_id()

        self.assertEqual(result, '1')

    

if __name__ == '__main__':
    unittest.main()
