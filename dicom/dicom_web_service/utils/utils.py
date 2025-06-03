import requests
import os
import pydicom
import io
import re

class DicomwebService():
    def __init__(self):
        self.output_list = []

    def create_folder_and_write_file(self, parent, folder_name, file_name, content):
        """
        Creates folder structure for model training.
        """
        folder_path = os.path.join(parent, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'wb') as file:
            file.write(content)

    def dicom_web_query(self, seriesurl, request_body, auth):
        """
        Queries for available DICOM data from DicomWeb Server using set of DICOM Tags and corresponsing values (PatientID is mandatory). 
        Args:
            seriesurl(str): URL to look for series present in DICOMWeb server. 
            request_body(dict): Request body from client containing DICOM Tag and corresponding value to search and retrieve data
            auth(list): List containing authentication params (Username, Password) to DICOM server
        Returns:
            dict: Response of the query operation
                A nested JSON with Series and Study UIDs available for each PatientID that matches the query.
        
        """
        valid_parameters = ["PatientID","PatientName","PatientBirthDate","PatientAge","StudyDescription","StudyDate","AccessionNumber","StudyInstanceUID","SeriesInstanceUID","Modality","StudyID","BodyPartExamined", "InstitutionName"]
        for key in request_body:
            if key not in valid_parameters:
                return {"status": 400, "Message": "Not a valid tag"}
        if request_body is None or len(request_body)==0:
            return {"status":400, "Message":"Request body is empty"}
        
        try:
            response = requests.get(seriesurl, params=request_body, auth=auth)
            print(response.json())
        except:
            return {'status': 404, 'message': 'DICOMWeb Server not available'}
        
        result = {}
        for val in response.json():
            patient_id = val["00100020"]["Value"][0]
            study_id= val["0020000D"]["Value"][0]
            series_id= val["0020000E"]["Value"][0]
            
            if patient_id not in result:
                result[patient_id] = {"PatientID": patient_id, "studies": []}

            current_patient = result[patient_id]["studies"]

            if not any(study["study_uid"] == study_id for study in current_patient):
                current_patient.append({"study_uid": study_id, "series": []})

            current_study = next(study for study in current_patient if study["study_uid"] == study_id)

            if series_id not in [series["series_uid"] for series in current_study["series"]]:
                current_study["series"].append({"series_uid": series_id})

        # Extracting the values from the result dictionary
        formatted_result = [{"PatientID": patient["PatientID"], "studies": patient["studies"]} for patient in result.values()]
        return {"message": formatted_result, "status":200}

    def dicom_web_retrieve(self, request_body, base_url, auth):
        """
        Retrieves DICOM series from DicomWeb Server using SeriesInstanceUID tag and anyother optional DICOM Tag if required. 
        Args:
            request_body(dict): Request body from client containing DICOM Tag and corresponding value to search and retrieve data
            base_url(str): URL to the DICOMWeb Server
            auth(list): List containing authentication params (Username, Password) to DICOM server
        Returns:
            dict: Response of the retrieve operation
            Returns MIME encoded DICOM byte data if success(200 status), else error message
        
        """
        if ("SeriesInstanceUID" in request_body):
            series_uid = request_body["SeriesInstanceUID"]
            if series_uid == "":
                return {"status":400, " Message":"Not Enough parameters"}
            else:
                search_url = f"{base_url}/series"
                response_studies = requests.get(search_url, params={"SeriesInstanceUID":series_uid}, auth = auth)
                studies = response_studies.json()
                for study in studies:
                    study_uid = study["0020000D"]["Value"][0]
                instances_url = f"{base_url}/studies/{study_uid}/series/{series_uid}/instances/"
                response_instances = requests.get(instances_url, auth = auth)
                instances = response_instances.json()
                for instance in instances:
                    instance_uid = instance["00080018"]["Value"][0]
                    instance_url = f"{base_url}/studies/{study_uid}/series/{series_uid}/instances/{instance_uid}/" 
                    instance = requests.get(instance_url,auth=auth)
                    self.output_list.append(io.BytesIO(self.decode_mime(instance.content)))
                return {"status": 200, "retrieved_data": self.output_list}       
        else:
            return {"status":400, " Message":"Not Enough parameters"}    
         
    def decode_mime(self, mime_bytes_msg):
        """
        Decodes DICOM data from MIME headers.
        Uses "DICM" prefix of the DICOM file that should be present starting at the 128th byte to find the beginning of the DICOM file
        Uses "content-type" value in MIME header to find the last byte of the dicom tag.
        Args:
            mime_bytes_msg: Mime enclosed dicom data
        Returns:
            Decoded DICOM data without mime headers and delimiters
        """

        for dicm in re.finditer(b'Content-Length:', mime_bytes_msg):
            content_length_index = dicm.end() + 1
            content_length = ''
            while mime_bytes_msg[content_length_index:content_length_index + 1].decode('utf-8').isdigit():
                content_length += mime_bytes_msg[content_length_index:content_length_index + 1].decode('utf-8')
                content_length_index += 1

        for dicm in re.finditer(b'DICM', mime_bytes_msg):
            start = dicm.start() - 128 #Go to the start of the DICOM data ['DICM' starts at 128th byte]

        decoded_dcm_data = mime_bytes_msg[start: start+int(content_length)]
        return decoded_dcm_data
    
    
    def separate_series(self, series):
        result = []
        for patient_data in series:
            # print(patient_data)
            patient_id = patient_data['PatientID']
            studies = patient_data['studies']
            
            for study in studies:
                study_uid = study['study_uid']
                series_list = study['series']
                
                for series_data in series_list:
                    series_uid = series_data['series_uid']
                    
                    patient_info = {
                        'PatientID': patient_id,
                        'StudyInstanceUID': study_uid,
                        'SeriesInstanceUID': series_uid
                    }
                    result.append(patient_info)
        
        return result
