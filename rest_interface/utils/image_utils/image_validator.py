import os
import pydicom
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
from utils.exceptions import *

class ImageQualityValidation:
    def __init__(self):
        self.accepted_height= 512
        self.accepted_width =512    

    def quality_validation_dicom_inferencing(self,byte_data):
        """
        Performs image quality validation on the dicom inference data.
        Arguments: byte_data: Dicom image data in bytes format.
        Returns(dict): A dictionary containing the result of the image quality validation on the inference image
                        which includes a status code and message. if the input inference image passed the quality validation ,returns
                        "Image Quality validation successful" with status code 200  
                        else, "Error. Image quality validation is not successful" with status code 400
        """
        resolution_validation_file=self.image_resolution_screening_dicom(byte_data)
        blank_file=self.blank_image_screening_dicom_inferencing(byte_data)
        if resolution_validation_file and blank_file:
            return {"status": 200, "message":"Image Quality validation successful"}
        else:
            return {"status": 400, "message":"Error. Image quality validation is not successful"}
        
    def quality_validation_non_dicom_inferencing(self,byte_data):
        """
        Performs image quality validation on the non-dicom inference data.
        Arguments: byte_data: non dicom image data in bytes format.
        Returns(dict): A dictionary containing the result of the image quality validation on the inference image
                        which includes a status code and message. if the input inference image passed the quality validation ,returns
                        "Image Quality validation successful" with status code 200  
                        else, "Error. Image quality validation is not successful" with status code 400
        """
        resolution_validation_file=self.image_resolution_screening_non_dicom(byte_data,)
        blank_file=self.blank_image_screening_non_dicom_inferencing(byte_data)
        if resolution_validation_file and blank_file:
            return {"status": 200, "message":"Image Quality validation successful"}
        else:
            return {"status": 400, "message":"Error. Image quality validation is not successful"}

    def quality_validation_screening_training_dataset(self,folder_path):
        """
        Performs image quality validation on the training data set.
        Arguments:folder_path (str): The path to the folder containing training data set.
        Returns:(dict): A dictionary containing the result of the image quality validation on the training data set
                    which includes a status code , message, and list of removed file path.
        """
        total_files=sum([len(files) for root, _, files in os.walk(folder_path)])
        files_low_resolution= self.remove_low_res_image_folder(folder_path)
        files_blank=self.remove_blank_image_folder(folder_path)
        files_duplicates =self.remove_duplicate_dicom_images(folder_path)
        removed_files = files_low_resolution + files_blank + files_duplicates
        if not(removed_files):
            return {"status": 200, "message":"Image Quality validation successful. All images passed image quality validation"}
        elif (len(removed_files) == total_files):
            return {"status": 400, "message": "Error. All images failed image quality validation and were removed from the dataset."}
        elif (len(removed_files) >= (total_files//2)):
            return {"status": 401, "message": "Warning. Half of the images did not satisfy image quality validation and were removed from the dataset.",
                "removed_files": removed_files}
        else:
            return {"status": 201, "message": f"{len(removed_files)} images failed image quality validation and were removed from the dataset", 
                    "removed_files": removed_files}
        
    def remove_duplicate_dicom_images(self, folder_path):
        """
        Function to check duplicate dicom images in the training dataset and removes it 
        Arguments: folder_path (str): The path to the folder containing training dataset.
        Returns: duplicates(list): A list of file paths for the removed duplicate DICOM images.
        Raises: Exception: If there is an error reading the DICOM file.
        """
        sop_instance_uids = {}
        duplicates = []
        for root,_,files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if pydicom.misc.is_dicom(file_path):
                        dicom_data = pydicom.dcmread(file_path, force=True)
                        sop_instance_uid = dicom_data.SOPInstanceUID
                        if sop_instance_uid in sop_instance_uids:
                            duplicates.append(file_path)
                            os.remove(file_path)
                        else:
                            sop_instance_uids[sop_instance_uid] = file_path  
                except Exception as e:
                    return f"Error reading: {e}"
        return duplicates
    
    def remove_blank_image_folder(self, folder_path):
        """
        Function to removes blank images from the training data.
        Arguments: folder_path (str): Path to the folder containing training data set.
        Returns: blank_images (list): A list of file paths for the removed blank image files.
        """
        blank_images = []
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                result = self.blank_image_screening_file(file_path) #calls the blank_image_screening_file method to check the input image contain image pizxel data or not
                if not result: #if image is blank
                    blank_images.append(file_path) # add the blank image file path to removed files list
                    os.remove(file_path)    
        return blank_images
    
    def remove_low_res_image_folder(self, folder_path):
        """
        Function to removes low resolution images from the training data.
        Arguments: folder_path (str): Path to the folder containing training data set.
        Returns: low_res_images (list): A list of file paths for the removed files with low resolution or which raises exceptions.
        """
        low_res_images = []
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)  
                try:
                    result = self.check_image_resolution_file(file_path) 
                    if not result:
                        low_res_images.append(file_path)
                        os.remove(file_path)
                except (FileFormatError, DicomNumpyConversionError, ImageNumpyConversionError):
                    low_res_images.append(file_path)
                    os.remove(file_path)
        return low_res_images

    def check_resolution(self,height,width):
        """
        Checks if the given image resolution meets the accepted height and width criteria.
        Arguments:height (int): Height of the image
                  width (int): Width of the image
        Returns: result (bool): True if both height and width are greater than or equal to 
                                accepted height and accepted width,False otherwise.
        """
        if height >= self.accepted_height and width >= self.accepted_width:
            return True
        else:
            return False

    def image_resolution_screening_dicom(self, image_bytes):
        """
        Performs image resolution screening on the dicom inference data.
        Arguments: image_bytes: Image data in bytes format.
        Returns(bool): return True if image passed the resolution screening, false if it failed.                            
        """
        try:
            ds = pydicom.dcmread(BytesIO(image_bytes), force=True)
            pixel_data = ds.pixel_array
            width, height = pixel_data.shape
            result = self.check_resolution(height, width)
            return result
        except AttributeError:
            # Handle the case where 'TransferSyntaxUID' attribute is not present
            # You can choose to log a warning or handle it differently based on your needs
            return False     
         
    def image_resolution_screening_non_dicom(self,image_bytes):
        """
        Performs image resolution screening on the non-dicom inference data.
        Arguments: image_bytes: non dicom image data in bytes format.
        Returns(bool): return True if image passed the resolution screening, false if it fails.                             
        """
        img = Image.open(BytesIO(image_bytes))
        width, height = img.size
        return self.check_resolution(height, width)
                 
    def blank_image_screening_dicom_inferencing(self,image_bytes):
        """
        Performs blank image screening on the dicom inference data.
        Arguments: image_bytes: Dicom image data in bytes format.
        Returns(bool): True if imageis not blank, false if it is blank.                      
        """
        dicom_array = self.convert_dicom_bytes_to_numpy(image_bytes)
        return not np.all(dicom_array == dicom_array[0])
               
    def blank_image_screening_non_dicom_inferencing(self,image_bytes):
        """
        Performs blank image screening on the non-dicom inference data.

        Arguments: image_bytes: Image data in bytes format.

        Returns(bool): return True if imageis not blank, false if it is blank.      
        """
        image_array = self.convert_non_dicom_bytes_to_numpy(image_bytes)
        return not(np.all(image_array == image_array[0]))
           
    def check_image_resolution_file(self, file_path):
        """
        Function to perform image resolution screening for inference data .

        Arguments: file_path (str): Path to the image file.

        Returns: result(bool)
                True, if the input image is greater than or equal to the stated resolution
                False , if the input image is less than the stated resolution
        
        Raises: FileFormatError:-If the file format is not supported ,other than DICOM, JPG, PNG, and BMP
                                        raises "File format is not valid."
        """
        extension = file_path.split(".")[-1]
        if pydicom.misc.is_dicom(file_path):
            result = self.check_image_resolution_dicom_file(file_path) # Performs resolution check for DICOM images
            return result
        elif extension in ["jpg", "png", "bmp"]:
            result = self.check_image_res_non_dicom_file(file_path) # Performs resolution check for Non-DICOM images
            return result
        else:
            raise FileFormatError("File format is not valid.")

    def check_image_resolution_dicom_file(self,file_path):  
        """
        Function to perform image resolution screening on dicom files

        Arguments:file_path (str): Path to the DICOM image file.

        Returns: True, if the DICOM image resolution is greater than or equal to the stated resolution
                False , if the DICOM image resolution is less than the stated resolution
    
        Raises: DicomNumpyConversionError: If there is an error converting the DICOM file to a NumPy array or if
                                       the DICOM array is None.
                Exception: If any other unexpected error occurs during the process.
        """ 
        try:
            dicom_array = self.convert_dcm_to_numpy(file_path)# calls the convert_dcm_to_numpy function
            if dicom_array is not None:
                height = dicom_array.shape[0]
                width = dicom_array.shape[1]
                return self.check_resolution(height,width) # calls the check_resolution function to check the input image passed the resolution criteria.
            else:
                raise DicomNumpyConversionError("Error converting DICOM to NumPy array or DICOM array is None.")
        except Exception as e:
            return f"Error: {e}"
            
    def check_image_res_non_dicom_file(self,file_path):
        """
        Function to perform image resolution screening on non-dicom files

        Arguments: file_path(str): Path to the non-DICOM image file.

        Returns:True, if the image resolution is greater than or equal to the stated resolution
                False , if the image resolution is less than the stated resolution
    
        Raises: ImageNumpyConversionError: If there is an error converting the non-DICOM file to a NumPy array or if
                            the image array is None.
                Exception: If any other unexpected error occurs during the process.
        """
        try:
            extension = file_path.split(".")[-1]
            image_array =self.convert_nondcm_to_numpy(file_path,file_type=extension)# call the convert_nondcm_to_numpy function
            if image_array is not None:
                height = image_array.shape[0]
                width = image_array.shape[1]
                return self.check_resolution(height,width)  # calls the check_resolution function to check the input image passed the resolution criteria.
            else:
                raise ImageNumpyConversionError("Error converting image to NumPy array or image array is None.")
        except Exception as e:
            return (f"Error: {e}")
              
    def blank_image_screening_file(self, file_path):
        """
        Checks the input image file contains image data or blank.

        Arguments:file_path (str): Path to the image file (DICOM or non-DICOM).

        Returns: (bool): True if the image is not blank,i.e ,pixel values are not same throughout the image
                         False ,if the image is blank, i.e, pixel values are same throughout the image

        Raises: Any exceptions raised during the image reading or conversion process.
        """
        try:
            #Check the input dicom image is blank or not
            if pydicom.misc.is_dicom(file_path):
                dicom_array = self.convert_dcm_to_numpy(file_path)# call the convert_dcm_to_numpy function
                return not(np.all(dicom_array == dicom_array[0]))    
            else:
                #Check the input image is blank or not for non-dicom images(jpg,png,bmp)
                extension = file_path.split(".")[-1]
                image_array =self.convert_nondcm_to_numpy(file_path,file_type=extension)# call the convert_nondcm_to_numpy function
                return not(np.all(image_array == image_array[0]))
        except Exception as e:
            return f"Error reading {file_path} : {e}"

    def convert_dcm_to_numpy (self, image_path):
        """
        Convert a DICOM image file to a NumPy array.
        Parameters:
        - image_path: Path to the DICOM image.
        Returns:
        - numpy_arr: NumPy array representing the image pixel data.
        """
        ds = pydicom.dcmread(image_path, force= True) 
        pixel_data = ds.pixel_array 
        rows = int(ds.Rows)
        cols = int(ds.Columns)
        numpy_arr = np.reshape(pixel_data, (rows, cols)) 
        return numpy_arr
    
    def convert_nondcm_to_numpy(self, img, file_type="bmp"):
        """
        Convert a non-DICOM image file (like JPG, PNG, BMP) to a NumPy array.
        Arguments:
        - img: Path to the non-DICOM image.
        - file_type: String specifying the type of the image file ('jpg', 'png', 'bmp'). Default is "bmp".
        Returns:
        - numpy_arr: NumPy array representing the image pixel data.
        Raises:
        -Raises FileFormatError as "Invalid image type", if files other than jpg,png,bmp is given as input
        """
        numpy_arr = None
        if file_type in ['jpg', 'png', 'bmp']:
            numpy_arr = cv2.imread(img)
            numpy_arr = cv2.cvtColor(numpy_arr, cv2.COLOR_BGR2RGB)
            return numpy_arr
        else:
            raise FileFormatError('Invalid image type')
        

    def convert_non_dicom_bytes_to_numpy(self,image_bytes):
        """
        Convert non dicom image bytes data  into numpy arary.
        Arguments:
        - image_bytes: non-dicom image data in bytes format.
        Returns:
        - image_arr: NumPy array representing the image pixel data.
        """
        image = Image.open(BytesIO(image_bytes))
        image_array = np.array(image)
        return image_array
    
    def convert_dicom_bytes_to_numpy(self, image_bytes):
        """
        Convert dicom image bytes data  into numpy arary.
        Arguments:
        - image_bytes: dicom image data in bytes format.
        Returns:
        - image_arr: NumPy array representing the image pixel data.
        """
        img_bytes = BytesIO(image_bytes)
        dcm_ds = pydicom.dcmread(img_bytes, force=True)   
        pixel_data = dcm_ds.pixel_array
        rows, cols = int(dcm_ds.Rows), int(dcm_ds.Columns)
        image_arr = np.reshape(pixel_data, (rows, cols))     
        return image_arr
