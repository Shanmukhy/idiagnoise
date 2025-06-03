from flask import jsonify, send_file,request
import requests
from utils.image_utils.preprocessing import ImageProcessing
from utils.image_utils.image_validator import ImageQualityValidation
from utils.image_utils.dicom2pdf import PdfGeneration
from utils.exceptions import *
import base64
import io
import numpy as np
import json
from pydicom.valuerep import PersonName
import shutil
from zipfile import ZipFile


class iDiagnoseRestAPI:
    
    def __init__(self, dicom, reporting, inference_server, cloud_server, scheme):
        (self.dicom_ip, self.dicom_port) = dicom
        (self.reporting_ip, self.reporting_port) = reporting
        (self.infer_ip, self.infer_port) = inference_server
        (self.cloud_ip, self.cloud_port) = cloud_server

        self.CLASSES_LIST = []
        self.dcm_as_pdf = True # default flag to convert DICOM image data as pdf
        self.scheme = scheme
        
    def feedback_request(self, data):
        dicom_url = self.scheme+self.cloud_ip+':'+str(self.cloud_port)+'/cloud-api/feedback'
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        if access_token:
            headers = {'Authorization': 'Bearer ' + access_token}
            response = requests.post(dicom_url, json=data,headers=headers)
            return response
        else:
        # Handle the case when Authorization header is not present
            return jsonify({'error': 'Authorization header not found'}), 401
    
    def test_request(self, data):
        api_url = 'http://127.0.0.1:10000/cloud-api/test/lungs-xray'
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        if access_token:
            headers = {'Authorization': 'Bearer ' + access_token}
            headers.update({'Content-Type': 'application/json'})
            response = requests.post(url=api_url, json=data, headers=headers)
            return response
        else:
            return jsonify({'error': 'Authorization header not found'}), 401
    
    def train_request(self, data):
        api_url = self.scheme + self.cloud_ip+":"+str(self.cloud_port)+"/cloud-api/train/"+str(data["train_data_id"])
        print(api_url)
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        if access_token:
            headers = {'Authorization': 'Bearer ' + access_token}
            headers.update({'Content-Type': 'application/json'})
            response = requests.post(url=api_url, json=data, headers=headers)
            return response
        else:
            return jsonify({'error': 'Authorization header not found'}), 401
    
    def examine_request(self, data):
        api_url = self.scheme+self.dicom_ip+':'+str(self.dicom_port)+'/api/examined-training-data'
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        if access_token:
            headers = {'Authorization': 'Bearer ' + access_token}
            response = requests.get(url=api_url, json=data,headers=headers)
            return response
        else:
            return jsonify({'error': 'Authorization header not found'}), 401

    def download_from_pacs(self, data):
        query_url = self.scheme+self.dicom_ip+':'+str(self.dicom_port)+'/api/query'
        retrieve_url = self.scheme+self.dicom_ip+':'+str(self.dicom_port)+'/api/retrieve'
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        if access_token:
            headers = {'Authorization': 'Bearer ' + access_token}
            response = requests.get(url=query_url, json=data, headers=headers)

            queries = []
            for patient in response.json():
                for study in patient['studies']:
                    for series in study['series']:
                        query_dict = {}
                        query_dict["PatientID"] = patient['PatientID']
                        query_dict["StudyInstanceUID"] = study['study_uid']
                        query_dict["SeriesInstanceUID"] = series['series_uid']
                    
                        queries.append(query_dict)

            files = []
            for query in queries:
                response = requests.get(url=retrieve_url, json=query, headers=headers)
                if response.status_code == 200:
                    files.append((f"{query['PatientID']}_{query['StudyInstanceUID']}_{query['SeriesInstanceUID']}", response.content))
            
            return files
        else:
            return jsonify({'error': 'Authorization header not found'}), 401

        
    def infer_request(self, data):
        api_url = self.scheme + self.infer_ip+':'+str(self.infer_port)+'/api/infer/lungs-xray'
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        if access_token:
            headers = {'Authorization': 'Bearer ' + access_token}
            headers.update({'Content-Type': 'application/json'})
            response = requests.post(url=api_url, json=data, headers=headers)
            return response
        else:
            return jsonify({'error': 'Authorization header not found'}), 401

    def search_get_request(self, pid):
        dicom_url = self.scheme+self.dicom_ip+':'+str(self.dicom_port)+'/api/query'
        report_url = self.scheme+self.cloud_ip+':'+str(self.cloud_port)+'/cloud-api/report/check-record'
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        headers = {'Authorization': 'Bearer ' + access_token}
        request_body = {"PatientID":str(pid)}
		
        response = requests.get(dicom_url, json=request_body, headers = headers)
        report_req = {
            "PatientID": str(pid),
            "SeriesUID" : None
        }
        if response.status_code == 200:
            if len(response.json()) > 0:
                series_uids = []

                # Traverse the list and extract series UIDs
                for patient_data in response.json():
                    for study_data in patient_data['studies']:
                        for series_data in study_data['series']:
                            series_uids.append(series_data['series_uid'])
                report_req = {
                    "PatientID": str(pid),
                    "SeriesUID": series_uids
                }
        report_resp = requests.post(report_url, json=report_req,headers=headers)
        return response, report_resp


    def search_post_request(self, data):
        pid = data['pid']
        self.request_body = data['series_data']

        report_req = {
            "PatientID": str(pid),
            "SeriesUID": self.request_body['SeriesInstanceUID']
        }

        api_url = self.scheme+self.dicom_ip+':'+str(self.dicom_port)+'/api/retrieve'
        report_url = self.scheme+self.cloud_ip+':'+str(self.cloud_port)+'/cloud-api/report/get-report'
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        headers = {'Authorization': 'Bearer ' + access_token}
        response = requests.get(api_url, json=self.request_body,headers=headers)
        if response.status_code == 200:
            report_resp = requests.post(report_url, json=report_req,headers=headers)
        else:
            response, report_resp = None, None
            
        return response, report_resp

    def validate_image(self, image_data, iv):

        if (iv.check_image_resolution_file(image_data) == False):
            raise ValueError("Image Resolution is not valid")
        elif(iv.is_not_blank_image_file(image_data) == False):
            raise(InvalidImageDataError("Image Data is blank."))
        return True


    def image_processing(self, img_data, imtype='dcm'):
        ip = ImageProcessing()
        iv = ImageQualityValidation()

        self.validate_image(img_data, iv)

        img_npy = ip.image_to_array(img_data, imtype)
        
    
        if (ip.validate_img_size((224, 224), img_npy.shape)):
            img_npy = ip.resize_array(img_npy, (224, 224))
            #img_npy = ip.normalize_img(img_npy)

            b64_img = base64.b64encode(img_npy)
            if img_npy.dtype == np.int16:
                dtype="int16"
            else:
                dtype="uint8"
            return b64_img, dtype

    def generate_report(self, dicom_data, ai_result):
        url = self.scheme+self.reporting_ip+':'+str(self.reporting_port)+'/report/create-interim-report'
        access_token = request.headers.get('Authorization').replace('Bearer ', '')

        files = {'dicom_data': ('dicom_data', dicom_data)}
        data = {'inference_results': json.dumps(ai_result)}
        headers = {'Authorization': 'Bearer ' + access_token}
        response = requests.post(url, files=files, data=data,headers=headers)

        try:
            result = response.json()
            print("JSON Respose:", result)
            return result
        except requests.exceptions.JSONDecodeError as e:
            print("Failed to decode JSON:", e)
            print("Raw Response Content:", response.content)
            return f"Failed to decode JSON: {e}"


    def inference_dicom(self, dicom_image, dtype):
        '''
            This function works for performing the inferncine
        '''
        api_url = self.scheme+self.infer_ip+':'+str(self.infer_port)+'/api/infer/lungs-xray'
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        headers = {'Authorization': 'Bearer ' + access_token}
        try:
            response = requests.post(
                url=api_url, json={'patient_dicom': str(dicom_image), 'dtype':dtype, 'fromSearch': True}, headers=headers) 

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise ValueError(response.json())
            else:
                raise ValueError(response.json())
        except Exception as e:
            print(f"Error: {str(e)}")
            
    
    def search_sr(self, data):
        dicom_query_url = self.scheme+self.dicom_ip+':'+str(self.dicom_port)+'/api/query'
        cloud_url = self.scheme+self.cloud_ip+':'+str(self.cloud_port)+'/cloud-api/report/get-patient-inference'

        pn = PersonName.from_named_components(family_name = data.get("lastname",""), given_name = data.get("firstname",""),
                                              name_prefix = data.get("name_prefix",""), name_suffix = data.get("name_suffix",""))
        
        dicom_query_body = {"PatientName" : str(pn), "PatientID" : data.get("pid", ""), "PatientBirthDate": data.get("dob","")}
        
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        headers = {'Authorization': 'Bearer ' + access_token}
        
        dicom_resp = requests.get(dicom_query_url, json=dicom_query_body, headers=headers)
        if dicom_resp.status_code == 200:
            dicom_studies = dicom_resp.json()
            if not dicom_studies:
                return None
            
            dicom_sr = dict()
            image_urls = dict()
            dicom_sr["studies"] = dicom_resp.json()
            
            series_uids = []
            for patient_data in dicom_resp.json():
                    for study_data in patient_data['studies']:
                        for series_data in study_data['series']:
                            series_uids.append(series_data['series_uid'])
            
            inferences = []
            images = []
            
            for id in series_uids:
                series_request = {"PatientID": data["pid"], "SeriesInstanceUID": id}
                report_resp = requests.get(cloud_url, json = series_request, headers = headers)
                if report_resp.status_code == 200:
                    current_inference = report_resp.json()["inference"]
                    current_image = report_resp.json()["image_path"]
                    if current_inference not in inferences:
                        inferences.append(current_inference)
                    if current_image not in images:
                        images.append(current_image)
                        
            dicom_sr["inferences"] = inferences
            image_urls["imageurl"] = images
            return dicom_sr, image_urls
        
        else:
            return jsonify(dicom_resp.json())
    

    def isAIEnabled(self, data):
        try:
            if data['AI_enabled'] is True:
                ai_infer = True
            elif data['AI_enabled'] is False:
                ai_infer = False
        except Exception as e:
            ai_infer = None
        return ai_infer
    
    
    def search_get(self, request):
        pid = request.json['pid']
        response,  report_resp = self.search_get_request(pid)
        if response.status_code == 200 and report_resp.status_code == 200:
            if len(response.json()) == 0:
                if report_resp.json()['record_available']:
                    return jsonify({"PACS_RESPONSE": "No record found in Query, but got the SR in Report Database. Please raise the request to clear the report."}), 200
                else:
                    return jsonify({"PACS_RESPONSE": "No Patient Data available, Please check the Patient ID passed in request."}), 200
            else: 
                if report_resp.json()['record_available']:
                    return_resp = {
                        "PACS_RESPONSE": response.json(),
                        "REPORT_CHECK": report_resp.json()
                    }
                else:
                    return_resp = {
                        "PACS_RESPONSE": response.json(),
                        "REPORT_CHECK": None
                    }
                return jsonify(return_resp), 200

        else:
            if response.status_code != 200:
                return jsonify(response.json()), response.status_code
            if report_resp.status_code != 200:
                return jsonify(response.json()), response.status_code
            
    def search_post(self, request):
        try:
            data = request.get_json()
            access_token = request.headers.get('Authorization').replace('Bearer ', '')
            headers = {
                "Authorization":'Bearer ' + access_token,
                     "Content-Type": "application/json"
                    }
            ai_infer = self.isAIEnabled(data)
            
            response, reporting_resp = self.search_post_request(data)
            if response is None:
                return jsonify({"Message":"Something wrong with the /api/retrieve"}), 200
            
            if self.dcm_as_pdf:
                dcm2pdf = PdfGeneration()
                image_data = dcm2pdf.byte_to_pdf(response.content)
                mimetype = 'application/pdf'
                filename = f"{self.request_body['SeriesInstanceUID']}.pdf"
            else:
                image_data = response.content
                mimetype = 'image/dicom'
                filename = f"{self.request_body['SeriesInstanceUID']}.dcm"

            b64_dicom_file = base64.b64encode(image_data).decode('utf-8')

            reporting_response = reporting_resp.json()
            if ai_infer:
                if not reporting_response['record_available']:
                    b64_img, dtype = self.image_processing(response.content)
                    res = self.inference_dicom(b64_img, dtype)
                    resp = self.generate_report(response.content, res)
                    json_payload = {
                        "imagefile" : b64_dicom_file,
                        "reportfile": resp['file'],
                        "PatientID": resp['PatientID'],
                        "SeriesInstanceUID": resp['SeriesInstanceUID'],
                        "inference_results": res["ai_result"]}
                    
                    try:
                        url = self.scheme+self.cloud_ip+':'+str(self.cloud_port)+'/cloud-api/report/update-interim-report'
                        response=requests.post(url,json=json_payload,headers=headers)
                        if response.status_code == 200:
                            return response.json()
                        elif response.status_code == 404:
                            return jsonify({"error": "Resource not found"}), 404
                        else:
                            return jsonify({"error": response.json()}), response.status_code
                    except Exception as e:
                        print(f"Error: {str(e)}")

                    if resp is not None:
                        return jsonify(resp), 200
                    return jsonify({'message': reporting_resp.json()}), 200
                return jsonify({'message': reporting_resp.json()}), 200

            else:
                print("Savingfile")
                return send_file(
                    io.BytesIO(image_data),
                    mimetype=mimetype,
                    as_attachment=True,
                    download_name=filename), 200
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def nlp_send_query(self, request, access_token):
        try:
            query = request["query"]
            inference = request["inference"]
            if query:
                request_body = {"query": query, "conditions": self.CLASSES_LIST,"inference":inference}
                api_url = self.scheme+self.reporting_ip+':'+str(self.reporting_port)+'/api/handle-query'
                headers = {'Authorization': 'Bearer ' + access_token}
                response = requests.get(url=api_url, json=request_body,headers=headers) 
                return response
            else:
                return None
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            