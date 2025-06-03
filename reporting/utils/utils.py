from PIL import Image, ImageDraw, ImageFont
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.sequence import Sequence
from pydicom.uid import UID
from pydicom.filebase import DicomFileLike
from datetime import datetime
import numpy as np
from io import BytesIO
import base64
import spacy


class InvalidFileFormatError(Exception):
    pass


class ReportGeneration:
    def extract_dicom_info(self, dicom_data):
        """
        Extracts relevant information from a DICOM file.

        Parameters:
        - dicom_data (bytes): The byte data of the DICOM file.

        Returns:
        dict: A dictionary containing the extracted information.
            {
                "PatientID": str,
                "PatientName": str,
                "PatientAge": str,
                "PatientGender": str,
                "ReferringPhysician": str,
                "StudyDateTime": str,
                "SeriesInstanceUID": str
            }
        """
        ds = pydicom.dcmread(BytesIO(dicom_data))
        patient_id = str(ds.PatientID)
        name = str(ds.PatientName)
        age = str(ds.PatientAge)
        gender = str(ds.PatientSex)
        series_uid = str(ds.SeriesInstanceUID)
        referring_physician = str(ds.ReferringPhysicianName)
        study_date = datetime.strptime(ds.StudyDate, "%Y%m%d")
        study_time = datetime.strptime(ds.StudyTime, "%H%M%S.%f")
        study_date_time = study_date.strftime("%d/%m/%Y") + '  ' + study_time.strftime("%H:%M:%S")
        return {
            "PatientID": patient_id,
            "PatientName": name,
            "PatientAge": age,
            "PatientGender": gender,
            "ReferringPhysician": referring_physician,
            "StudyDateTime": study_date_time,
            "SeriesInstanceUID": series_uid
        }
    
    def dcm_to_numpy(self, dicom_data):
        """
        Convert DICOM data to a NumPy array representing pixel data.

        Parameters:
        - dicom_data (bytes): The byte data of the DICOM file.

        Returns:
        numpy.ndarray: A NumPy array representing the pixel data extracted from the DICOM file.

        Raises:
        - InvalidFileFormatError: If the provided data is not in DICOM format.
        - ValueError: If no file data is provided.
        """
        if dicom_data is not None:
            try:
                ds = pydicom.dcmread(BytesIO(dicom_data), force=True)
                return ds.pixel_array
            except pydicom.errors.InvalidDicomError:
                raise InvalidFileFormatError("Invalid file format. Expected DICOM file")
        else:
            raise ValueError("No file data provided")

    def numpy_to_image(self, pixel_array):
        """
        Convert a NumPy array representing pixel data to an image.

        Parameters:
        - pixel_array (numpy.ndarray): The NumPy array containing pixel data.

        Returns:
        PIL.Image.Image: The image created from the pixel array.
        """
        pixel_array = pixel_array.astype(np.float32)
        pixel_array = (pixel_array / np.max(pixel_array)) * 255
        pixel_array = pixel_array.astype(np.uint8)
        image = Image.fromarray(pixel_array) # numpy array to image
        return image
    
    def overlay_text(self, dicom_data, inference_result, position=(50, 60), font_size=90, font_color="White", font_path=None):
        """
        Overlay text on an image generated from DICOM pixel data.

        Parameters:
        - dicom_data (bytes): The byte data of the DICOM file.
        - inference_result (str): The text to overlay on the image.
        - position (tuple): The position where the text should be overlayed, default is (50, 60).
        - font_size (int): The font size of the overlay text, default is 90.
        - font_color (str): The color of the overlay text, default is "White".
        - font_path (str): The path to the font file, default is None.

        Returns:
        PIL.Image.Image: The image with the overlay text.

        Raises:
        - InvalidFileFormatError: If the provided data is not in DICOM format.
        - ValueError: If no file data is provided.
        """
        self.inference = inference_result
        try:
            pixel_array = self.dcm_to_numpy(dicom_data)
            image = self.numpy_to_image(pixel_array)
            image = image.convert("RGB")
            draw = ImageDraw.Draw(image)
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.load_default()

            draw.text(position, inference_result, fill=font_color, font=font)
            return image
        except Exception as e:
            print("Error:" , e)

    def generate_report(self, inference_results, dicom_data):
        """
        Generate an intermediate report in PDF format.

        Parameters:
        - inference_results (str): The AI findings or results to be included in the report.
        - dicom_data (bytes): The byte data of the DICOM file.

        Returns:
        str or None: If successful, returns the file path of the generated PDF.
                    If unsuccessful or missing DICOM information, returns None.
        """
        dicom_info = self.extract_dicom_info(dicom_data)
        if dicom_info:
            name = dicom_info['PatientName']
            age = dicom_info['PatientAge']
            gender = dicom_info['PatientGender']
            physician = dicom_info['ReferringPhysician']
            study_date_time = dicom_info['StudyDateTime']
            pixel_array = self.dcm_to_numpy(dicom_data) #get pixel array
            image = self.numpy_to_image(pixel_array)
            image.thumbnail((380, 450))  # resize image data
            text_image = self.overlay_text(dicom_data, inference_results, position=(50,60), font_size=90, font_color="White", font_path=None)
            # create a blank pdf
            pdf_page = Image.new("RGB", (1000, 600), "white")
            pdf_draw = ImageDraw.Draw(pdf_page)
            # metadata info
            metadata_text = f"Patient's Name                : {name} ({age}/{gender})\n" \
                            f"Physician's Name          : {physician}\n" \
                            f"Study Date and Time  : {study_date_time}\n" \
                            f"Image Data                        :"
            pdf_draw.text((50, 50), metadata_text, fill="black", size= 20)
            # Render AI findings
            pdf_draw.text((50, 150), f"AI Findings : {inference_results}", fill="black", size = 18)            
            # the 'Intermediate Report' note
            date_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            pdf_draw.text((50, 530), f"Report Generated on :{date_time}", fill= "black", size= 12)
            pdf_draw.text((50, 550),
                          "The Report is Intermediate and not verified by a clinical specialist",
                          fill="red", size = 12)
            pdf_page.paste(text_image, (450, 150)) # paste image into PDF            
            # Save pdf
            output_file = "Intermediate_Report.pdf"
            pdf_page.save(output_file)
            return output_file
        else:
            return None


class GenAIChatBot(ReportGeneration):
    def __init__(self, conditions):
        self.threshold = 0.5 
        self.nlp = spacy.load("en_core_web_sm")
        self.medical_keywords=conditions

    def handle_query(self, user_input):
        """
        Handles the user's input and executes the corresponding intent function.

        Argument:
            user_input (str): The user's input.

        Returns:
            dict or str: The result of the executed intent function or a message.
        """
        doc=self.nlp(user_input.lower())
        classification_keywords = ["sign","suffer","symptom","signs","suffering","symptoms"]
        # medical_conditions = [condition.lower() for condition in self.medical_keywords]
        for conditions in self.medical_keywords:
            for class_words in classification_keywords:
                if conditions.lower() in doc.text and class_words in doc.text:
                    result= self.get_medical_keywords(doc)  
                    return result
        return "Insufficient data"
        
    
    def get_medical_keywords(self,doc):
        """
        Extracts the medical keyword from the document.

        Argument:
            doc (spacy.Doc): The processed Spacy document.

        Returns:
            str or None: The extracted medical keyword or None if not found.
        """
        keyword=None
        for token in doc:
            for keyword_condition in self.medical_keywords:
                if token.text == keyword_condition.lower():
                    keyword = token.text
                    return keyword  


    def query_inference_result(self, keyword, inference):
        """
        Queries the inference result for a specific medical keyword.

        Argument:
            keyword (str): The medical keyword to query.

        Returns:
            str: A message indicating the presence or absence of the medical condition.
        """
        self.inference = inference
        if isinstance(self.inference, dict):
            inference_result = {key.lower(): value.lower() if isinstance(value, str) else value for key, value in self.inference.items()}
            if keyword in inference_result:
                if inference_result[keyword]>=self.threshold :
                    return f"The patient shows signs of {keyword} (confidence:{inference_result[keyword]})."
                elif inference_result[keyword] < self.threshold :
                    conditions_present = [(key, value) for key, value in inference_result.items() if value >= self.threshold]
                    if conditions_present:
                        condition_confidence = [f"{condition} (confidence:{confidence})" for condition, confidence in conditions_present]
                        return f"Patient doesn't shows signs of {keyword}.But there is signs of {', '.join(condition_confidence)}."
                    else:
                        return f"There is no signs of {keyword} (confidence:{inference_result[keyword]})."

        if isinstance(self.inference, str):
            if keyword == self.inference:
                return f"The patient shows signs of {keyword}."
            else:
                return f"The patient does not show signs of {keyword}."
        else:
            return "Not enough data"
        

class ContentItem:
    """
    ContentItem Class to create DICOM content item objects.
    DICOM Content Items represent individual pieces of information or content within a DICOM structured report (SR).
    Content Items are organized hierarchically, forming a tree structure where these items can hold different types of information.

    Example usage:
    1. To create content item without value
        code_item = ContentItem("CODE", "SCHEME", "Content")
    2. To create content item with TEXT value
        finding_content_item = ContentItem("CODE", "SCHEME", "Content", "TEXT", "SampleText")
    3. To create content item with NUMERIC value
        numerical_content_item = ContentItem("CODE", "SCHEME", "Value", "NUM", 100)
    """
    def __init__(self, code_value, coding_scheme_designator, code_meaning, value_type = None, value = None):
        """
        Initialize ContentItem Object

        Args:
            code_value (str): DICOM Code Value.
            coding_scheme_designator (str): DICOM Code Scheme Designator.
            code_meaning (str): Meaning of the code in human readable form.
            value_type (str, optional): DICOM Value type corresponsing to the Code. Can be "TEXT", "NUM", "CODE", "DATETIME", "DATE", "TIME", "UIDREF". Defaults to None
            value (Union[int, str], optional): Value of the content item. Defaults to None.
        Returns:
            None
        """
        self.code_value = code_value
        self.coding_scheme_designator = coding_scheme_designator
        self.code_meaning = code_meaning
        if (value_type is not None) and (value is not None):
            self.value_type = value_type
            self.value = value

    def get_dicom_ds(self):
        """
        Creates pydicom dataset from code values ContentItem
        Returns:
            pydicom.dataset.Dataset: Pydicom dataset containing codes without value and value_type
        Usage: 
            Used to create pydicom dataset that contain only codes to which value type and value can be added later. 
            Useful to create code sequences for containers and other content items. 
            Containers are content items that hold multiple content items
        """
        ds = Dataset()
        ds.CodeValue = self.code_value
        ds.CodingSchemeDesignator = self.coding_scheme_designator
        ds.CodeMeaning = self.code_meaning
        return ds
    
    def get_content_item(self):
        """
        Creates complete content item as a pydicom dataset. Should not be used for creating containers. 
        Returns: 
            pydicom.dataset.Dataset: Pydicom dataset containing complete content items
        """
        content_item = Dataset()
        content_item.ConceptNameCodeSequence = Sequence([self.get_dicom_ds()])
        content_item.ValueType = self.value_type
        if self.value_type == "TEXT":
            content_item.TextValue = str(self.value)
        elif self.value_type == "NUM":
            content_item.NumericValue = int(self.value)
        elif self.value_type == "DATETIME":
            content_item.DateTime = str(self.value)
        elif self.value_type == "DATE":
            content_item.Date = str(self.value)
        elif self.value_type == "TIME":
            content_item.Time = str(self.value)
        elif self.value_type == "UIDREF":
            content_item.UID = UID(self.value)
        elif self.value_type == "CODE":
            content_item.ConceptCodeSequence = Sequence([self.value.get_dicom_ds()])
        else:
            content_item.TextValue = str(self.value)
        return content_item
    

class SrUtils():
    """
    DICOM Structured Reporting Utilities class containing various methods to support DICOM SR creation
    """
    def create_container(self, code, content_item_list):
        """
        Creates DICOM Structured Report container that can hold content items
        Args:
            code (ContentItem): DICOM Content Item Object
            content_item_list (list): List of content_items that should be part of the container
        Returns:
            pydicom.dataset.Dataset: DICOM Structured Report Container containing content items
        """
        container = Dataset()
        container.ConceptNameCodeSequence = Sequence([code.get_dicom_ds()])
        container.ContentSequence = content_item_list
        return container
    
    def create_template(self):
        """
        Creates a DICOM Structured Report template with pre-coded values
        Returns:
            pydicom.dataset.Dataset: DICOM Structured Report Template in which inference results and imaging related data are filled. 
        """
        sop_class_uid = "1.2.840.10008.5.1.4.1.1.88.11"
        sop_instance_uid = pydicom.uid.generate_uid()
        template_meta = FileMetaDataset()
        template_meta.TransferSyntaxUID = UID("1.2.840.10008.1.2.1")
        template_meta.MediaStorageSOPInstanceUID = sop_instance_uid
        template_meta.MediaStorageSOPClassUID = UID(sop_class_uid)

        template_ds = Dataset()
        template_ds.SOPClassUID = UID(sop_class_uid)
        template_ds.SOPInstanceUID = UID(sop_instance_uid)
        template_ds.file_meta = template_meta

        template_ds.ReferencedPerformedProcedureStepSequence = Sequence([Dataset()])
        template_ds.SpecificCharacterSet = 'ISO_IR 100'
        template_ds.Manufacturer = "iDiagnose"
        template_ds.Modality = 'SR'
        template_ds.InstanceNumber = '1'
        template_ds.CompletionFlag = "COMPLETE"
        # Verification Flag should be UNVERIFIED
        # UNVERIFIED because the final DICOM SR document is not verified by anyone
        # ONLY the inference results from AI are verified, not the final SR document. 
        template_ds.VerificationFlag = "UNVERIFIED"  
        dt = datetime.now()
        template_ds.ContentDate = dt.strftime('%Y%m%d')
        time = dt.strftime('%H%M%S')  # long format with micro seconds
        template_ds.ContentTime = time
        template_ds.ReferencedSOPSequence = Sequence([Dataset()])
        template_ds.is_little_endian = True
        template_ds.is_implicit_VR = False
        return template_ds
    
    def _get_value_type_from_string(self, input_str):
        """
        Private method to check whether an input string contains a number. Should not be accessed outside this class
        Args:
            input_str(str): Input String.
        Returns:
            str: "NUM" if input_str is a number within a string, "TEXT" if otherwise.
        """
        try:
            float(input_str)
            return "NUM"
        except ValueError:
            return "TEXT"
        
    def sr_items_from_cad(self, cad_inference):
        """
        Creates a list of content items from CAD inference results. 
        If CAD inference results are not available or empty, the value stored is "Not Available"
        Args:
            cad_inference(list|str): Findings obtained from CAD inference.Can be a list of findings, or a string
        Returns:
            list: List containing content item for each CAD finding.
        """
        findings = []
        if len(cad_inference) == 0:
            cad_inference.append("Not Available")  #Append "Not Available" to inference if cad_inference is empty
        if isinstance(cad_inference, str):
            #create content item dataset with finding
            content_item = ContentItem("121071", "DCM", "Finding", "TEXT", cad_inference).get_content_item()  
            findings.append(content_item)
        elif isinstance(cad_inference, list):
            for finding in cad_inference:
                #create content item dataset with findings
                content_item = ContentItem("121071", "DCM", "Finding", "TEXT", finding).get_content_item()  
                findings.append(content_item)
        return findings

    def sr_items_from_user(self, user_inference):
        """
        Creates list of content items from user inputs given as key-value pairs in a dictionary. 
        If CAD inference results are not available or empty, the value stored is "Not Available"
        Args:
            cad_inference(list): List of findings obtained from CAD inference.
        Returns:
            list: List containing DICOM content item for each CAD finding.
        """
        items = []
        for key,value in user_inference.items():
            valtype = self._get_value_type_from_string(value)
            content_item = ContentItem("00000", "IDX", key, valtype, value).get_content_item()
            items.append(content_item)
        return items
    
    def fill_template_with_dicom(self, report_ds, dicom_bytes):
        """
        Copies crucial DICOM Tags from DICOM Image to DICOM SR
        Args:
            report_ds (pydicom.dataset): Report Data in the form of pydicom dataset
            dicom_bytes (bytes): Image DICOM data as bytes
        """
        image_ds = pydicom.dcmread(BytesIO(dicom_bytes))
        self.patient_id = image_ds.PatientID
        self.series_uid = image_ds.SeriesInstanceUID
        for tag in ["PatientID", "PatientName", "PatientSex", "PatientBirthDate", "StudyInstanceUID", "StudyDate", "StudyTime", "StudyID", "ReferringPhysicianName", "AccessionNumber"]:
            if tag in image_ds:
                report_ds[tag] = image_ds[tag]
            else:
                setattr(report_ds, tag, "")
        report_ds.ReferencedSOPSequence[0].ReferencedSOPClassUID = image_ds.SOPClassUID
        report_ds.ReferencedSOPSequence[0].ReferencedSOPInstanceUID = image_ds.SOPInstanceUID

    def create_dicom_sr(self, inference, dicom_bytes):
        """
        Function to create DIOCM SR from DICOM Image data and inference data from CAD and User Inputes
        Args:
            inference (dict): Inference results and additional inputs from user
            dicom_bytes (bytes): Image DICOM data as bytes
        Returns:
            pydicom.dataset: Final DICOM Structured Report Data in the form of pydicom dataset     
        """
        dcm_ds = self.create_template()
        self.fill_template_with_dicom(dcm_ds, dicom_bytes)
        finding_items = self.sr_items_from_cad(inference["cad_inference"])
        
        header_code = ContentItem("CAD", "DCM", "Diagnosis Report")
        c_findings = ContentItem("0000", "IDX", "CAD Findings") 
        cad_findings_header = self.create_container(c_findings, finding_items)
        
        if inference["user_inference"] == {}:
            container = self.create_container(header_code, [cad_findings_header])
        else:   
            u_findings = ContentItem("0000", "IDX", "HCP Inputs")
            other_items = self.sr_items_from_user(inference["user_inference"])
            user_findings_header = self.create_container(u_findings, other_items)
            container = self.create_container(header_code, [cad_findings_header, user_findings_header])
        dcm_ds.ContentSequence = [container]
        return dcm_ds
    
    def dicom_ds_to_b64(self, dataset):
        """
        Converts pydicom.Dataset object to byte data. Used to create base64 data to send as API response
        Args:
            dataset (pydicom.dataset): DICOM Structured Report Dataset as pydicom dataset object
        Returns:
            bytes: Base64 Encoded pydicom dataset object
        """
        with BytesIO() as buffer:
            memory_dataset = DicomFileLike(buffer)
            pydicom.dcmwrite(memory_dataset, dataset, write_like_original = False)
            memory_dataset.seek(0)
            base64_encoded = base64.b64encode(memory_dataset.read())
            return base64_encoded