import unittest
from unittest.mock import patch
from utils.image_utils.image_validator import ImageQualityValidation, FileFormatError
import numpy as np
import pydicom



class TestImageQualityValidation(unittest.TestCase):

    def setUp(self):
        self.image_quality_validation = ImageQualityValidation()

    @patch('utils.image_utils.image_validator.ImageQualityValidation.image_resolution_screening_dicom')
    @patch('utils.image_utils.image_validator.ImageQualityValidation.blank_image_screening_dicom_inferencing')
    def test_quality_validation_dicom_inferencing_successful(self, mock_blank_screening, mock_resolution_screening):
        file_path = "tests/datas/IMG001.dcm"
        with open(file_path, 'rb') as file:
            actual_dicom_data = file.read()
        mock_resolution_screening.return_value = True
        mock_blank_screening.return_value = True
        
        result = self.image_quality_validation.quality_validation_dicom_inferencing(actual_dicom_data)
        self.assertEqual(result, {"status": 200, "message": "Image Quality validation successful"})

    @patch('utils.image_utils.image_validator.ImageQualityValidation.image_resolution_screening_dicom')
    @patch('utils.image_utils.image_validator.ImageQualityValidation.blank_image_screening_dicom_inferencing')
    def test_quality_validation_dicom_inferencing_failure(self, mock_blank_screening, mock_resolution_screening):
        mock_resolution_screening.return_value = False
        mock_blank_screening.return_value = True
        file_path ="tests/datas/IMG002.dcm"
        with open(file_path, 'rb') as file:
            dicom_data = file.read()  
        result = self.image_quality_validation.quality_validation_dicom_inferencing(dicom_data)
        self.assertEqual(result, {"status": 400, "message": "Error. Image quality validation is not successful"})

    @patch('utils.image_utils.image_validator.ImageQualityValidation.image_resolution_screening_non_dicom')
    @patch('utils.image_utils.image_validator.ImageQualityValidation.blank_image_screening_non_dicom_inferencing')
    def test_quality_validation_non_dicom_inferencing_successful(self, mock_blank_screening, mock_resolution_screening):
        mock_resolution_screening.return_value = True
        mock_blank_screening.return_value = True
        file_path = "tests/datas/IMG001.jpg"
        with open(file_path, 'rb') as file:
            dicom_data = file.read()  
        result = self.image_quality_validation.quality_validation_non_dicom_inferencing(dicom_data)
        self.assertEqual(result, {"status": 200, "message": "Image Quality validation successful"})

    @patch('utils.image_utils.image_validator.ImageQualityValidation.image_resolution_screening_non_dicom')
    @patch('utils.image_utils.image_validator.ImageQualityValidation.blank_image_screening_non_dicom_inferencing')
    def test_quality_validation_non_dicom_inferencing_res_failure(self, mock_blank_screening, mock_resolution_screening):
        mock_resolution_screening.return_value = False #low res
        mock_blank_screening.return_value = True #non-blank
        file_path = "tests/datas/IMG002.jpg"
        with open(file_path, 'rb') as file:
            dicom_data = file.read()  
        result = self.image_quality_validation.quality_validation_non_dicom_inferencing(dicom_data)
        self.assertEqual(result, {"status": 400, "message": "Error. Image quality validation is not successful"})

    @patch('utils.image_utils.image_validator.ImageQualityValidation.image_resolution_screening_non_dicom')
    @patch('utils.image_utils.image_validator.ImageQualityValidation.blank_image_screening_non_dicom_inferencing')
    def test_quality_validation_non_dicom_inferencing_failure_blank(self, mock_blank_screening, mock_resolution_screening):
        mock_resolution_screening.return_value = True 
        mock_blank_screening.return_value = False
        file_path ="tests/datas/black.bmp"
        with open(file_path, 'rb') as file:
            dicom_data = file.read()  
        result = self.image_quality_validation.quality_validation_non_dicom_inferencing(dicom_data)
        self.assertEqual(result, {"status": 400, "message": "Error. Image quality validation is not successful"})

    @patch('utils.image_utils.image_validator.ImageQualityValidation.check_image_resolution_dicom_file')
    def test_check_image_resolution_file_dicom_pass(self, mock_check_dicom_res):
        mock_check_dicom_res.return_value = True
        result = self.image_quality_validation.check_image_resolution_file("tests/datas/IMG001.dcm")
        self.assertTrue(result)

    @patch('utils.image_utils.image_validator.ImageQualityValidation.check_image_resolution_dicom_file')
    def test_check_image_resolution_file_dicom_fail(self, mock_check_dicom_res):
        mock_check_dicom_res.return_value = False
        result = self.image_quality_validation.check_image_resolution_file("tests/datas/IMG002.dcm")
        self.assertFalse(result)

    @patch('utils.image_utils.image_validator.ImageQualityValidation.check_image_res_non_dicom_file')
    def test_check_image_resolution_file_non_dicom_pass(self, mock_check_non_dicom_res):
        mock_check_non_dicom_res.return_value = True
        result = self.image_quality_validation.check_image_resolution_file("tests/datas/IMG001.jpg")
        self.assertTrue(result)

    @patch('utils.image_utils.image_validator.ImageQualityValidation.check_image_res_non_dicom_file')
    def test_check_image_resolution_file_non_dicom_fail(self, mock_check_non_dicom_res):
        mock_check_non_dicom_res.return_value = False
        result = self.image_quality_validation.check_image_resolution_file("tests/datas/IMG002.jpg")
        self.assertFalse(result)

    def test_check_image_training_successful(self):
        with patch('os.walk') as mock_walk:
            folder_path = "tests/datas/validation_successful"
            mock_walk.return_value = [(folder_path, [],[])]
            with patch.object(self.image_quality_validation, 'remove_low_res_image_folder', return_value=[]):
                with patch.object(self.image_quality_validation, 'remove_blank_image_folder', return_value=[]):
                    with patch.object(self.image_quality_validation, 'remove_duplicate_dicom_images', return_value=[]):
                        result = self.image_quality_validation.quality_validation_screening_training_dataset(folder_path)
                        expected_result = {"status": 200, "message": "Image Quality validation successful. All images passed image quality validation"}
                        self.assertEqual(result, expected_result)


    def test_check_image_training_half_failed(self):
        with patch('os.walk') as mock_walk:
            folder_path = "tests/datas/validation_failed"
            mock_walk.return_value = [(folder_path, [],[])]
            with patch.object(self.image_quality_validation, 'remove_low_res_image_folder', return_value=["tests/datas/validation_failed/class A/IMG03.jpg","tests/datas/validation_failed/class A/IMG01.png"]):
                with patch.object(self.image_quality_validation, 'remove_blank_image_folder', return_value=["tests/datas/validation_failed/class B/blank3.dcm"]):
                    with patch.object(self.image_quality_validation, 'remove_duplicate_dicom_images', return_value=[]):
                        result = self.image_quality_validation.quality_validation_screening_training_dataset(folder_path)
                        expected_result = {"status": 401, "message": "Warning. Half of the images did not satisfy image quality validation and were removed from the dataset.", "removed_files": ["tests/datas/validation_failed/class A/IMG03.jpg","tests/datas/validation_failed/class A/IMG01.png","tests/datas/validation_failed/class B/blank3.dcm"]}
                        self.assertEqual(result, expected_result)

    @patch('utils.image_utils.image_validator.ImageQualityValidation.convert_dcm_to_numpy')
    def test_blank_image_screening_file_dicom_blank(self, mock_convert_dcm):
        mock_convert_dcm.return_value = np.array([[1, 1], [1, 1]])
        result = self.image_quality_validation.blank_image_screening_file("tests/datas/blank3.dcm")
        # Assert that the result is False (blank)
        self.assertFalse(result)

    @patch('utils.image_utils.image_validator.ImageQualityValidation.convert_dcm_to_numpy')
    def test_blank_image_screening_file_dicom_non_blank(self, mock_convert_dcm):
        mock_convert_dcm.return_value = np.array([[1, 2], [3, 4]])
        result = self.image_quality_validation.blank_image_screening_file("tests/datas/IMG001.dcm")
        # Assert that the result is True (non-blank)
        self.assertTrue(result)

    @patch('utils.image_utils.image_validator.ImageQualityValidation.convert_nondcm_to_numpy')
    def test_blank_image_screening_file_non_dicom_non_blank(self, mock_convert_nondcm):
        mock_convert_nondcm.return_value = np.array([[1, 2], [3, 4]])
        result = self.image_quality_validation.blank_image_screening_file("tests/datas/IMG001.jpg")
        # Assert that the result is True (non-blank)
        self.assertTrue(result)

    @patch('utils.image_utils.image_validator.ImageQualityValidation.convert_nondcm_to_numpy')
    def test_blank_image_screening_file_non_dicom_blank(self, mock_convert_nondcm):
        mock_convert_nondcm.return_value = np.array([[1, 1], [1, 1]])
        result = self.image_quality_validation.blank_image_screening_file("tests/datas/black.bmp")
        # Assert that the result is false (blank)
        self.assertFalse(result)

    @patch('utils.image_utils.image_validator.ImageQualityValidation.convert_dcm_to_numpy')
    @patch('utils.image_utils.image_validator.ImageQualityValidation.check_resolution')
    def test_check_image_resolution_dicom_file_pass(self, mock_check_resolution, mock_convert_dcm):
        mock_convert_dcm.return_value =  np.array([[1, 2], [3, 4]])
        mock_check_resolution.return_value =True 
        result = self.image_quality_validation.check_image_resolution_dicom_file("tests/datas/ct.dcm")
        self.assertTrue(result)

    @patch('utils.image_utils.image_validator.ImageQualityValidation.convert_dcm_to_numpy')
    @patch('utils.image_utils.image_validator.ImageQualityValidation.check_resolution')
    def test_check_image_resolution_dicom_file_fail(self, mock_check_resolution, mock_convert_dcm):
        mock_convert_dcm.return_value = np.array([[1, 2], [3, 4]])
        mock_check_resolution.return_value = False 
        result = self.image_quality_validation.check_image_resolution_dicom_file("tests/datas/IMG002.dcm")
        self.assertFalse(result)

    @patch('utils.image_utils.image_validator.ImageQualityValidation.convert_nondcm_to_numpy')
    @patch('utils.image_utils.image_validator.ImageQualityValidation.check_resolution')
    def test_check_image_resolution_non_dicom_file_pass(self, mock_check_resolution, mock_convert_dcm):
        mock_convert_dcm.return_value =  np.array([[1, 1], [1, 1]])
        mock_check_resolution.return_value = True 
        result = self.image_quality_validation.check_image_res_non_dicom_file("tests/datas/IMG001.jpg")
        self.assertTrue(result)

    @patch('utils.image_utils.image_validator.ImageQualityValidation.convert_nondcm_to_numpy')
    @patch('utils.image_utils.image_validator.ImageQualityValidation.check_resolution')
    def test_check_image_resolution_non_dicom_file_fail(self, mock_check_resolution, mock_convert_dcm):
        mock_convert_dcm.return_value = np.array([[1, 2], [3, 4]]) 
        mock_check_resolution.return_value = False
        result = self.image_quality_validation.check_image_res_non_dicom_file("tests/datas/IM002.jpg")
        self.assertFalse(result)

    def test_check_image_resolution_file_invalid_format(self):
        with self.assertRaises(FileFormatError):
            self.image_quality_validation.check_image_resolution_file("tests/datas/test.txt")
    
    def test_dcm_to_numpy(self):
        # You may need to provide a valid DICOM file path for testing
        paths = ["tests/datas/ct.dcm", "tests/datas/ilowres1.dcm"]
        for dcm_file_path in paths:
            ds = pydicom.dcmread(dcm_file_path)
            numpy_array = self.image_quality_validation.convert_dcm_to_numpy(dcm_file_path)
            self.assertIsInstance(numpy_array, np.ndarray)
            self.assertEqual(numpy_array.shape[0], ds.Rows)
            self.assertEqual(numpy_array.shape[1], ds.Columns)

    def test_nondcm_to_numpy(self):
        image_file_path = "tests/datas/test_image.jpg"
        numpy_array = self.image_quality_validation.convert_nondcm_to_numpy(image_file_path)
        self.assertIsInstance(numpy_array, np.ndarray)

    def test_dcmbytes_to_numpy(self):
        path = "tests/datas/ct.dcm"
        dcm_bytes = open(path, "rb").read()
        numpy_array = self.image_quality_validation.convert_dicom_bytes_to_numpy(dcm_bytes)
        assert isinstance(numpy_array, np.ndarray)

    def test_nondcmbytes_to_numpy(self):
        path = "tests/datas/test_image.jpg"
        dcm_bytes = open(path, "rb").read()
        numpy_array = self.image_quality_validation.convert_non_dicom_bytes_to_numpy(dcm_bytes)
        assert isinstance(numpy_array, np.ndarray)

    def test_check_resolution(self):
        self.assertTrue(self.image_quality_validation.check_resolution(512, 512))
        self.assertTrue(self.image_quality_validation.check_resolution(513, 513))
        self.assertFalse(self.image_quality_validation.check_resolution(511, 511))
        self.assertFalse(self.image_quality_validation.check_resolution(0, -1))

    def test_image_resolution_screening_nondcm(self):
        path = "tests/datas/IMG003.jpg"
        byte_data = open(path, "rb").read()
        self.assertFalse(self.image_quality_validation.image_resolution_screening_non_dicom(byte_data))

    def test_image_resolution_screening_dcm(self):
        path = "tests/datas/ilowres1.dcm"
        byte_data = open(path, "rb").read()
        self.assertFalse(self.image_quality_validation.image_resolution_screening_dicom(byte_data))

    def test_blank_screening(self):
        path = "tests/datas/black.bmp"
        byte_data = open(path, "rb").read()
        self.assertFalse(self.image_quality_validation.blank_image_screening_non_dicom_inferencing(byte_data))

        path = "tests/datas/blank3.dcm"
        byte_data = open(path, "rb").read()
        self.assertFalse(self.image_quality_validation.blank_image_screening_dicom_inferencing(byte_data))
