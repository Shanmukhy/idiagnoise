import cv2
import numpy as np
import pydicom
import io
from PIL import Image

class InvalidFileFormatError(Exception):
    pass

class ImageQualityError(Exception):
    pass

class ImageProcessing():
    def __init__(self):
        pass
    
    def validate_img_size(self, nw_shape, img_shape):
        """
        Validate whether two image shapes are equal.

        Parameters:
       - nw_shape: Tuple representing the shape of the new image (height, width).
       - img_shape: Tuple representing the shape of the original image (height, width).

       Returns:
       - bool: True if the shapes of the new image and the original image are equal, else False.

       Notes:
       - 'nw_shape' and 'img_shape' are tuples containing height and width dimensions respectively.
       - Compares the height and width dimensions of the new image ('nw_shape') with the original image ('img_shape').
       - Returns True if both height and width dimensions are equal between the two shapes; otherwise, returns False.
        """
        return (nw_shape[0] == img_shape[0]) and (nw_shape[1] == img_shape[1])
    
    def validate_pixel_quality(self, numpy_array, byte_data):
        """
         Validate the quality of a given image represented as a NumPy array against the original image bytes.

         Parameters:
         - numpy_array: NumPy array representing the image data.
         - byte_data: Bytes data of the original image.

         Returns:
         - bool: True if the deviation between the original image and the NumPy array is less than 1%, else False.

         Notes:
         - Converts the 'bytes' data into a NumPy array using 'np.frombuffer'.
         - Decodes the 'img_bytes' using OpenCV's 'cv2.imdecode' to obtain an image.
         - Calculates the absolute difference between the decoded image and 'numpy_array' using 'cv2.absdiff'.
         - Computes the mean value of the absolute differences using 'np.mean'.
         - Determines the maximum pixel value in the decoded image using 'np.amax'.
         - Calculates the deviation percentage between the mean value and the maximum pixel value.
         - Returns True if the deviation percentage is less than 1%, indicating good pixel quality; otherwise, False.
         """
        img_bytes = np.frombuffer(byte_data, dtype= np.uint8)
        img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        abs_diff = cv2.absdiff(img , numpy_array) #absolute difference
        mean = np.mean(abs_diff)  #mean value
        max_pixel = np.amax(img)
        dev_percent = (mean/max_pixel) * 100
        return dev_percent < 1   # returns true if deviation < 1%
    
    def dcm_to_numpy(self, image_path):
        """
        Convert a DICOM image file to a NumPy array.

        Parameters:
        - image_path: File path of the DICOM image.

        Returns:
        - numpy_arr: NumPy array representing the image pixel data.

        Raises:
        - InvalidFileFormatError: If the provided file is not a valid DICOM file.

        Notes:
        - Checks if the file at 'image_path' is a valid DICOM file using 'pydicom.misc.is_dicom'.
        - If the file is a DICOM file, reads it using 'pydicom.dcmread' with 'force=True'.
        - Calls 'get_imagearray_from_dcmdataset' to extract the pixel array data and convert it to a NumPy array.
        - The resulting 'numpy_arr' represents the image pixel data in a NumPy array format.
        """
        if pydicom.misc.is_dicom(image_path):
            ds = pydicom.dcmread(image_path, force= True)
            return self.get_imagearray_from_dcmdataset(ds)
        else:
            raise InvalidFileFormatError("Invalid file format. Expected DICOM file")
    
    def nondcm_to_numpy(self, img, file_type = "bmp"):
        """
        Convert a non-DICOM image file (like JPG, PNG, BMP) to a NumPy array.

        Parameters:
        - img: File path of the non-DICOM image.
        - file_type: String specifying the type of the image file ('jpg', 'png', 'bmp'). Default is "bmp".

        Returns:
        - numpy_arr: NumPy array representing the image pixel data.

        Raises:
        - InvalidFileFormatError: If the provided file type is not supported or not a valid non-DICOM format.

        Notes:
       - Checks if the 'type' parameter corresponds to supported image file formats: 'jpg', 'png', 'bmp'.
       - Uses OpenCV's 'cv2.imread' to read the image file into a NumPy array.
       - Adjusts color channel ordering from BGR to RGB using 'numpy_arr[:, :, ::-1]'.
       - The resulting 'numpy_arr' represents the image pixel data in a NumPy array format.
        """
        numpy_arr = None
        if file_type in ['jpg', 'png', 'bmp']:
            numpy_arr = cv2.imread(img)
            if numpy_arr is not None:
                numpy_arr = numpy_arr[:, :, ::-1]
            else:
                raise InvalidFileFormatError("Invalid file format or path")
            return numpy_arr
        else:
            raise InvalidFileFormatError("Invalid file format. Expected non DICOM file")
        
    def image_to_array(self, data_bytes, img_type = "dcm"):
        """
        Convert an image to a NumPy array.

        Parameters:
         - data_bytes: Input image data, either a file path (str) or bytes data.
         - img_type: Type of the image; can be "dcm" (for DICOM) or image formats like "png", "jpg", "bmp".

        Returns:
         - img_array: NumPy array representing the image.

        Raises:
         - ValueError: If the image data or format is not supported.
         - ImageQualityError: If the image quality validation fails.

        Notes:
         - For DICOM images ('img_type' = "dcm"):
         - If 'image' is a file path, it's converted to a NumPy array using 'dcm_to_numpy' method.
         - If 'image' is bytes data, it's read as a DICOM dataset using 'pydicom.dcmread'.
           The pixel array is obtained using 'get_imagearray_from_dcmdataset'.
           Image quality is validated using 'validate_pixel_quality' method.
         - For non-DICOM images (image formats like 'png', 'jpg', 'bmp'):
         - If 'image' is a file path, it's converted to a NumPy array using 'nondcm_to_numpy' method.
         - If 'image' is bytes data, it's opened as an image using 'PIL.Image.open' and converted to a NumPy array.
           Image quality is validated using 'validate_pixel_quality' method.
        """
        if img_type == "dcm":
            if isinstance(data_bytes, str):
                img_array = self.dcm_to_numpy(data_bytes)
                return img_array
            elif isinstance(data_bytes, bytes):
                img_bytes = io.BytesIO(data_bytes)
                dcm_ds = pydicom.dcmread(img_bytes,force = True)
                img_array = self.get_imagearray_from_dcmdataset(dcm_ds)
                if self.validate_pixel_quality(img_array, data_bytes):
                    return img_array
                else:
                    raise ImageQualityError("Image quality validation failure")
            else:
                raise ValueError("Unsupported image data")

    def normalize_img(self, img_array):
         """
         Normalize a NumPy array representing image data to the [0, 1] range.

         Parameters:
         - img_array: NumPy array representing the image data.

         Returns:
         - norm_img: Normalized NumPy array representing the image data in the [0, 1] range.

         Notes:
         - Converts the 'img_array' to 'float32' for maximum precision.
         - Finds the maximum value within the 'img_array' using 'np.amax'.
         - Normalizes the image array by dividing it by the maximum value, ensuring values are in the [0, 1] range.
         - The resulting 'norm_img' represents the image data normalized between 0 and 1.
         """
         img = img_array.astype(np.float32)
         max_value = np.amax(img)
         norm_img = img/max_value
         return norm_img
    
    def get_imagearray_from_dcmdataset(self, dataset):
         """
         Extracts image pixel array data from a DICOM dataset and reshapes it into a NumPy array.

         Parameters:
         - dataset: DICOM dataset containing pixel data.

         Returns:
         - numpy_arr: NumPy array representing the image pixel data.

         Notes:
         - Extracts the pixel array data from the DICOM 'dataset' using 'dataset.pixel_array'.
         - Retrieves the number of rows and columns from the DICOM 'dataset.Rows' and 'dataset.Columns'.
         - Reshapes the pixel data using 'np.reshape' to form a NumPy array with dimensions (rows, cols).
         - The resulting 'numpy_arr' represents the image pixel data in a NumPy array format.
        """
         pixel_data = dataset.pixel_array
         rows = int(dataset.Rows)
         cols = int(dataset.Columns)
         numpy_arr = np.reshape(pixel_data, (rows, cols))
         return numpy_arr
		 
	
    def resize_array(self, img, shape):
        """
        Resize the input image array to the specified shape using bicubic interpolation.

        Parameters:
        - img: Input image array to be resized.
        - shape: Tuple specifying the desired shape of the output image array (height, width).

        Returns:
        - Resized image array with the specified shape.
        
        Notes:
        Bicubic interpolation is a high-quality method commonly used for image resizing. It produces smoother
        results compared to other interpolation methods like bilinear interpolation. The 'cv2.INTER_CUBIC' flag
        is used with OpenCV's resize function to perform bicubic interpolation.
        """
      
        img = cv2.resize(img, shape, cv2.INTER_CUBIC)
        return img
