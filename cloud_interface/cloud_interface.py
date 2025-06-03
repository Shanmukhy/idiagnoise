import requests
from flask import Flask, request, jsonify, send_file ,send_from_directory,session
import os
import json
import base64
import argparse
import logging
import yaml
from datetime import datetime,timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_jwt_extended import jwt_required, get_jwt_identity
from cloud.api import CloudInterface
from utils.mongo_collect import MongoCollection
from utils.Docker_start import Docker
from cloud.train_api import TrainDataStorage
from cloud.test_api import TestDataStorage
from cloud.report_api import ReportMaintainanceStorage
from utils.config import config


config_instance=config()
cloud_interface_instance = CloudInterface() 
Mongo_collect = MongoCollection() 
docker_instance= Docker()
train_instance=TrainDataStorage()
test_instance=TestDataStorage()
report_instance=ReportMaintainanceStorage()

app = Flask(__name__)
with open('config/auth_config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)
app.config['JWT_SECRET_KEY'] = config['development']['jwt_secret_key']
jwt = JWTManager(app)
app.logger.setLevel(logging.INFO)
ap = argparse.ArgumentParser()


ap.add_argument("-local","--docker_image",help="Docker images for training")
args = vars(ap.parse_args())

@app.route('/cloud-api/test-data/lungs-xray', methods=['POST'])
@jwt_required()
def test_data_lungs():
    try:
        current_user = get_jwt_identity() 
        app.logger.info(f"logged in as:{current_user}")
        if 'file' not in request.files:
            return jsonify({'message': 'No file part in the request'}), 400

        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400
        
        temp_file_path = os.path.join(os.getcwd(), file.filename)
        file.save(temp_file_path)
   
        try:
            blob_name,test_storage_id,timestamp_str=test_instance.generate_name(prefix="test_data")
            with open(temp_file_path, 'rb') as file_data:
                blob_url= test_instance.upload_blob(config_instance.train_container,blob_name,file_data)
                result=Mongo_collect.Test_data_DB_update(test_storage_id,blob_url,blob_name,timestamp_str)
                    
            app.logger.info(f"File uploaded to Azure Blob Storage with name: {blob_name}")
            response_data = { 'test_storage_id': test_storage_id}
            return jsonify(response_data), 200
          
        except Exception as ex:
            app.logger.error(f"Error uploading to Blob Storage: {str(ex)}")
            return jsonify({'message': 'Error uploading to Azure Blob Storage'}), 500

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500
 

@app.route('/cloud-api/train-data/lungs-xray', methods=['POST'])
@jwt_required()
def train_data_lungs():
    try:
        current_user = get_jwt_identity() 
        app.logger.info(f"logged in as:{current_user}")     
        if 'file' not in request.files:
            return jsonify({'message': 'No file part in the request'}), 400

        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400
        
        temp_file_path = os.path.join(os.getcwd(), file.filename)
        file.save(temp_file_path)   
        try:
            blob_name,train_storage_id,timestamp_str=train_instance.generate_name(prefix="train_data")
            with open(temp_file_path, 'rb') as file_data:
                blob_url=train_instance.upload_blob(config_instance.train_container,blob_name,file_data)
                inserted_id = Mongo_collect.Train_data_DB_update(train_storage_id, blob_url, blob_name,timestamp_str)
             
            app.logger.info(f"File uploaded to Azure Blob Storage with name: {blob_name}")
            response_data = { 'train_storage_id': train_storage_id}
            return jsonify(response_data), 200
        except Exception as ex:
            app.logger.error(f"Error uploading to Blob Storage: {str(ex)}")
            return jsonify({'message': 'Error uploading to Azure Blob Storage'}), 500

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/cloud-api/report/get-report', methods=['POST'])
@jwt_required()
def get_report():
    try:
        current_user = get_jwt_identity() 
        app.logger.info(f"logged in as:{current_user}")
        data = request.get_json()
        
        patient_id = data['PatientID']
        series_id = data['SeriesUID']
        # Check if the patient ID already exists
        patient_data = Mongo_collect.report_mongo_collection.find({"Patient_ID": patient_id})
        patient_list = list(patient_data)
        series_data = Mongo_collect.report_mongo_collection.find_one({"Patient_ID": patient_id, "SeriesUID": series_id}) #To check if series ID belongs to the patient ID
        if patient_list:
            if series_data:
                return_data = Mongo_collect.build_dicom_return_json(series_data)
                return jsonify({"record_available": True, "new_series_id": False, 'data': return_data}), 200
            else:
                return jsonify({"record_available": True, "new_series_id": True}), 200
        else:
             return jsonify({"record_available": False}), 200

    except Exception as e:
        return jsonify({"Error": str(e)}), 500

@app.route('/cloud-api/report/check-record', methods=['POST'])
@jwt_required()
def check_report():
    try:
        current_user = get_jwt_identity() 
        app.logger.info(f"logged in as:{current_user}")
        data = request.get_json()
        patient_id = data['PatientID']

        patient_data = Mongo_collect.report_mongo_collection.find({"Patient_ID": patient_id})
        patient_list = list(patient_data)
        
        pacs_series_uids = data['SeriesUID']
        mongo_series_uids = [item['SeriesUID'] for item in patient_list]
        
        if patient_list:
            if sorted(mongo_series_uids) == sorted(pacs_series_uids):
                return jsonify({"record_available": True, "new_series_id": False}), 200
            else:
                return jsonify({"record_available": True, "new_series_id": True}), 200
        else:
             return jsonify({"record_available": False}), 200
    except Exception as e:
        return jsonify({"Error": str(e)}), 500

@app.route('/cloud-api/deletion', methods=['POST'])
@jwt_required()
def delete_record():
    try:
        current_user = get_jwt_identity() 
        app.logger.info(f"logged in as:{current_user}")
        data = request.get_json()  
        Mongo_collect.delete_record(data)
        return jsonify({"message":"successfully deleted record"}), 200

    except Exception as e:
        logging.error(f"Error: {str(e)}")  
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/cloud-api/report/update-interim-report',methods=['POST'])
@jwt_required()
def update_report():
    try:
        current_user = get_jwt_identity() 
        app.logger.info(f"logged in as:{current_user}")
        data = request.get_json()
        encoded_dicom = data.get('imagefile')
        encoded_pdf = data.get('reportfile')
        patient_id = data.get('PatientID')
        series_id = data.get('SeriesInstanceUID')
        inference_results = data.get("inference_results")

        pdf_bytes = base64.b64decode(encoded_pdf)
        image_bytes = base64.b64decode(encoded_dicom)

        dcm_blobname= f"image_{patient_id}_{series_id}"
        report_blobname = f"report_{patient_id}_{series_id}.pdf"
        
        report_success = report_instance.upload_b64_to_cloud(pdf_bytes, report_blobname, "report")
        image_success = report_instance.upload_b64_to_cloud(image_bytes, dcm_blobname, "image")
        if report_success and image_success:
            return_data = Mongo_collect.update_record(patient_id,series_id,inference_results,report_blobname,dcm_blobname)
            return jsonify(return_data), 200
        else:
            return jsonify({"error": "Unable to upload report to cloud"}), 400

    except Exception as e:
        return jsonify({"error":str(e)}), 500

@app.route('/cloud-api/train/<string:train_storage_id>', methods=['POST'])
@jwt_required()
def start_train(train_storage_id):
    print(train_storage_id)
    try:
        current_user = get_jwt_identity() 
        app.logger.info(f"logged in as:{current_user}")
        docker_image_name = args["docker_image"]
        params = request.get_json()
        if docker_instance.is_image_present(docker_image_name):
            print(f"Image is present locally.")
            docker_instance.start_container_by_id(train_storage_id, docker_image_name, params)
            return jsonify({'message':'successfully started the training container'})
        else:
            return jsonify({"error":"Image not found locally."}), 404
    except Exception as e:
        logging.error(f"Error: {str(e)}")      
        return jsonify({"error": str(e)}), 500

@app.route('/client-api/report/get-patient-records', methods=['GET'])
@jwt_required()
def get_patient_records():
    try:
        current_user = get_jwt_identity() 
        app.logger.info(f"logged in as:{current_user}")
        patient_records=Mongo_collect.get_patient_records()
        return jsonify({"patient_records": patient_records}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/cloud-api/feedback', methods=['POST'])
@jwt_required()
def feedback_update():
    try:
        current_user = get_jwt_identity() 
        app.logger.info(f"logged in as:{current_user}")
        data = request.json
        for feedback in data:
            for record in feedback["records"]:
                try:
                    Mongo_collect.post_feedback(record["PID"], record["SeriesUID"], feedback["hcpInput"])
                except Exception as e:
                    return jsonify({"Error": str(e)}), 400
        return jsonify({"message": "Feedback processed successfully"}), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/cloud-api/test-data/<test_storage_id>/download', methods=['POST'])
@jwt_required()
def download_test_data(test_storage_id):
    try:
        current_user = get_jwt_identity() 
        app.logger.info(f"logged in as:{current_user}")
        if request.method == 'POST':
            if test_storage_id != '':
                download_url=Mongo_collect.get_test_url(test_storage_id)
                return jsonify({'message': 'download the test data','url':download_url}),200   
            else:
                latest_url=cloud_interface_instance.download_latest(config_instance.train_container)
                return jsonify({'message': 'download the test data','url':latest_url}),200
                                    
    except Exception as e:
        logging.error(f"Error: {str(e)}")


@app.route('/cloud-api/model/<version_id>/download-link', methods=['POST'])
@jwt_required()
def download_url(version_id):
    current_user = get_jwt_identity() 
    app.logger.info(f"logged in as:{current_user}")
    if version_id != '':
        download_url= Mongo_collect.download_link(version_id)
        return jsonify({'message': 'download the model','url':download_url}),200            
    else:
        latest_url=cloud_interface_instance.download_latest(config_instance.model_container)
        return jsonify({'message': 'download the model','url':latest_url}),200
    

@app.route('/cloud-api/list/model-info', methods=['POST'])
@jwt_required()
def list_version_id():
    current_user = get_jwt_identity() 
    app.logger.info(f"logged in as:{current_user}")
    version_ids = Mongo_collect.get_model_info()
    return jsonify({"version_ids": version_ids})


@app.route('/cloud-api/report/get-patient-inference', methods = ['GET'])
@jwt_required()
def get_db_inference():
    try:
        current_user = get_jwt_identity() 
        app.logger.info(f"logged in as:{current_user}")
        data = request.get_json()
        patient_id = data['PatientID']
        series_uid = data['SeriesInstanceUID']
        out = Mongo_collect.search_db_record(patient_id, series_uid)
        if out:
            return out, 200
        else:
            return jsonify({"message": "No matching data"}), 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/cloud-api/manage-pacs-studies', methods = ['GET', 'POST'])
@jwt_required(refresh=True)
def study_list_handler():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        if (request.method == 'GET'):
            app.logger.info("Getting PACS studies list from database")
            if Mongo_collect.dicomstudies_mongo_collection.count_documents({}) == 0:
                return jsonify({"message": "Dicom Studies list is empty"}), 204
            else:
                out = Mongo_collect.get_dicom_study_list()
                return jsonify({"series":out}), 200
            
        elif (request.method == 'POST'):
            app.logger.info("Updating new PACS studies list to Database")
            data = request.get_json()
            out = Mongo_collect.dicomstudies_mongo_collection.insert_many(data["series"])
            if out.acknowledged:
                return jsonify({"message":"Series list added to DB successfully"}), 200
            else:
                return jsonify({"message":"Could not update series list to DB"}), 500
            
    except Exception as e:
        print("Or here")
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8050, debug=True)
    