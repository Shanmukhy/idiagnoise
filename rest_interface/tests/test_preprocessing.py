import unittest
import numpy as np
from PIL import Image
from io import BytesIO
from utils.image_utils.preprocessing import ImageProcessing, ImageQualityError, InvalidFileFormatError
import cv2
import pydicom

class TestImageProcessing(unittest.TestCase):

    def setUp(self):
        self.image_processing = ImageProcessing()

    def test_validate_img_size(self):
        nw_shape = (100, 200)
        img_shape = (100, 200)
        self.assertTrue(self.image_processing.validate_img_size(nw_shape, img_shape))

        nw_shape = (150, 150)
        img_shape = (100, 200)
        self.assertFalse(self.image_processing.validate_img_size(nw_shape, img_shape))

    def test_validate_pixel_quality(self):
        original_bytes = open('tests/datas/test_image.jpg', 'rb').read()
        numpy_array = cv2.imread("tests/datas/test_image.jpg")
        self.assertTrue(self.image_processing.validate_pixel_quality(numpy_array, original_bytes))

        numpy_array_with_deviation = numpy_array + 10 #Add deviation to check if it returns false
        self.assertFalse(self.image_processing.validate_pixel_quality(numpy_array_with_deviation, original_bytes))

    def test_dcm_to_numpy(self):
        # You may need to provide a valid DICOM file path for testing
        paths = ["tests/datas/ct.dcm", "tests/datas/ilowres1.dcm"]
        for dcm_file_path in paths:
            ds = pydicom.dcmread(dcm_file_path)
            numpy_array = self.image_processing.dcm_to_numpy(dcm_file_path)
            self.assertIsInstance(numpy_array, np.ndarray)
            self.assertEqual(numpy_array.shape[0], ds.Rows)
            self.assertEqual(numpy_array.shape[1], ds.Columns)

    def test_dcm_to_numpy_exception(self):
        with self.assertRaises(InvalidFileFormatError):
            out = self.image_processing.dcm_to_numpy("tests/datas/test_image.jpg")

    def test_nondcm_to_numpy(self):
        image_file_path = "tests/datas/test_image.jpg"
        numpy_array = self.image_processing.nondcm_to_numpy(image_file_path)
        self.assertIsInstance(numpy_array, np.ndarray)

        with self.assertRaises(InvalidFileFormatError):
            numpy_array = self.image_processing.nondcm_to_numpy(image_file_path, "dcm")

    def test_image_to_array_filepath(self):
        out = self.image_processing.image_to_array("tests/datas/ct.dcm", img_type = "dcm")
        assert isinstance(out, np.ndarray)

    def test_normalize_img(self):
        img_array = np.random.randint(0, 255, size=(100, 100, 3), dtype=np.uint8)
        norm_img = self.image_processing.normalize_img(img_array)
        self.assertTrue(np.amax(norm_img) <= 1.0)

        img_array = 255.*np.ones((100,100,3), dtype=np.uint8)
        norm_img = self.image_processing.normalize_img(img_array)
        self.assertTrue(np.all(norm_img == norm_img[0]))

    def test_resize_array(self):
        img_array = np.random.randint(0, 255, size=(110, 90, 3), dtype=np.uint8)
        shape = (50, 50)
        resized_img = self.image_processing.resize_array(img_array, shape)
        self.assertEqual(resized_img.shape[0], shape[0])
        self.assertEqual(resized_img.shape[1], shape[1])


if __name__ == '__main__':
    unittest.main()
