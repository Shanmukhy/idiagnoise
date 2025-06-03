from flask import Flask, request, jsonify, send_file
from utils.config import Config
from rest.api import iDiagnoseRestAPI
from utils.zip_utils import ZipManager
from utils.image_utils.image_validator import ImageQualityValidation
from utils.exceptions import *
import requests
import os
import shutil
from apscheduler.schedulers.background import BackgroundScheduler
import yaml
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_refresh_token
from collection.user_management import UserManagement
import logging
from datetime import timedelta
import io
from zipfile import ZipFile

app = Flask(__name__)

cfg = Config("./config/microservice_conf.json")
dicom_ip, dicom_port = cfg.get_server_port_ip('dicom_server')
dicomweb_ip, dicomweb_port = cfg.get_server_port_ip('dicomweb_server')
reporting_ip, reporting_port = cfg.get_server_port_ip('reporting_server')
infer_ip, infer_port = cfg.get_server_port_ip('infer_server')
cloud_ip, cloud_port = cfg.get_server_port_ip('cloud_server')

with open('config/auth_config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)
ssl_enabled = config['development']['ssl_enabled']
scheme = "http://"
if ssl_enabled:
    scheme = "https://"

rest = iDiagnoseRestAPI((None, None), 
                        (reporting_ip, reporting_port), 
                        (infer_ip, infer_port), 
                        (cloud_ip, cloud_port),
                        scheme)

app.secret_key = config['development']['jwt_secret_key']
app.config['JWT_SECRET_KEY'] = config['development']['jwt_secret_key']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = False
jwt = JWTManager(app)
app.logger.setLevel(logging.INFO)
user_manager=UserManagement()

# Register a user
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    return user_manager.register_user(username, password)

# Login endpoint
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    return user_manager.login_user(username, password)

#PACS connection
@app.route('/api/configure-pacs', methods=['POST'])
@jwt_required()
def configure_pacs():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        if access_token:
            headers = {'Authorization': 'Bearer ' + access_token}
            data = request.get_json()
            if data["pacsType"] == "dicomweb":
                rest.dicom_ip = dicomweb_ip
                rest.dicom_port = dicomweb_port
                url = scheme + dicomweb_ip + ":" + str(dicomweb_port) + "/api/configure"
                response = requests.post(url, json = data["config"], headers = headers)
            elif data["pacsType"] == "dimse":
                rest.dicom_ip = dicom_ip
                rest.dicom_port = dicom_port
                url = scheme + dicom_ip + ":" + str(dicom_port) + "/api/configure"
                response = requests.post(url, json = data["config"], headers = headers)
            else:
                return jsonify({"message": "Unknown Server Type"}), 500
            
            return response.json(), response.status_code
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
#SearchSR API to search for existing patient reports
@app.route('/api/search-sr', methods = ['POST'])
@jwt_required()
def search_sr():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        data = request.get_json()
        out = rest.search_sr(data)
        if out:
            if data["AI_Outcome"]:
                return jsonify({"PatientID": data["pid"], "dicomsr": out[0], "image_path": out[1]["imageurl"]}), 200
            else:
                return jsonify({"PatientID": data["pid"], "image_path": out[1]["imageurl"]}), 200
        else:
            return jsonify({"message": "Query does not match any records"}), 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST', "GET"])
@jwt_required()
def search_patient():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        if (request.method == 'GET'):
            return rest.search_get(request)
            
        elif (request.method == 'POST'):
            return rest.search_post(request)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/infer/lungs-xray', methods=['POST'])
@jwt_required()
def infer_lungs():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        data = request.get_json()
        if data['fromSearch'] == False:
            files = request.files['file']
            if data['img_type'] in ['jpg', 'bmp', 'png', 'dcm']:
                b64_img, dtype = rest.image_processing(files, data['img_type'])
                data = {'patient_dicom': str(b64_img), 'dtype':dtype}
            else:
                raise FileFormatError("Provided file format "+data['img_type']+' is not supported.')

        if (request.method == 'POST'):
            response = rest.infer_request(data)
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": "Unknown request method."}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/train', methods=['POST'])
@jwt_required()
def train_lungs():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        data = request.get_json()
        if (request.method == 'POST'):
            response = rest.train_request(data)
            return jsonify(response.json()), response.status_code
        else:
            return jsonify({"error": "Unknown method type."}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/train-data/lungs-xray', methods=['POST','GET'])
@jwt_required()
def train_data_lungs():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        if (request.method == 'GET'):
            data = request.get_json()
            if data["transfer_learning"]:
                response = rest.examine_request(data)
                return jsonify(response.json()), response.status_code
            else:
                response = rest.download_from_pacs(data)
                if isinstance(response, list):
                    with io.BytesIO() as b:
                        with ZipFile(b, 'w') as zip_file:
                            for filename, content in response:
                                zip_file.writestr(filename, content)
                        zip_data = b.getvalue()
                
                    with open('data.zip', 'wb') as f:
                        f.write(zip_data)
                    return send_file('data.zip', as_attachment=True, download_name='extracted_data.zip'), 200
                else:
                    return response
        
        elif (request.method == 'POST'):
            if 'file' not in request.files:
                return jsonify({'message': 'No file part in the request'}), 400
    
            file = request.files['file']
            if file.filename == '':
                return jsonify({'message': 'No selected file'}), 400
    
            temp_file_path = os.path.join(os.getcwd(), 'train_data.zip')
            
            zip = ZipManager(file)
            zip.write(temp_file_path)
            zip.extract('train_data/')
            zip.validate_dataset()
            
            iv = ImageQualityValidation()
            res = iv.quality_validation_screening_training_dataset("./train_data/")
            rest.CLASSES_LIST = os.listdir('train_data/')
            if (res['status'] != 200):
                raise InvalidImageDataset(res['message'])
    
            upload_url = scheme + cloud_ip+':'+str(cloud_port)+'/cloud-api/train-data/lungs-xray'
            if access_token is not None:
                headers = {'Authorization': 'Bearer ' + access_token}
                with open(temp_file_path, 'rb') as file:
                    files = {'file': file}
                    response = requests.post(upload_url, files=files,headers=headers)

                    if response.status_code == 200:
                        train_id = response.json().get('train_storage_id', None)
                        shutil.rmtree('train_data/')
                        return jsonify({'train_storage_id': train_id}), 200
                    else:
                        return jsonify({'message': f'Error uploading file to the other endpoint: {response.text}'}), 500
    
    except Exception as e:
        app.logger.error(f"Error in train_data_lungs(): {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/test/lungs-xray', methods=['POST'])
@jwt_required()
def test_lungs():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        data = request.get_json()
        if (request.method == 'POST'):
            response = rest.test_request(data)
            jsonify(response.json()), response.status_code
        else:
            return jsonify({"error": "Unknown method type."}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-data/lungs-xray', methods=['POST'])
@jwt_required()
def test_data_lungs():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        if 'file' not in request.files:
            return jsonify({'message': 'No file part in the request'}), 400
 
        file = request.files['file']
 
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400
 
        temp_file_path = os.path.join(os.getcwd(), 'test_data.zip')
        
        zip = ZipManager(file)
        zip.write(temp_file_path)
        zip.extract('./test_data/')
        zip.validate_dataset()
        
        iv = ImageQualityValidation()
        res = iv.quality_validation_screening_training_dataset("./test_data/")
        if (res['status'] != 200):
            raise InvalidImageDataset(res['message'])

        dir_list = os.listdir("./test_data/")
        if len(dir_list) != rest.NUM_CLASSES:
            raise FileNotFoundError("Directory Structure is invalid.")
        if sorted(dir_list) != sorted(rest.CLASSES_LIST):
            raise FileNotFoundError("Directory Structure is invalid.")
 
        upload_url = scheme + cloud_ip+':'+str(cloud_port)+'/cloud-api/test-data/lungs-xray'
        if access_token is not None:
            headers = {'Authorization': 'Bearer ' + access_token}
        
            with open(temp_file_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(upload_url, files=files,headers=headers)
            
                if response.status_code == 200:
                    test_id = response.json().get('test_storage_id', None)
                    
                    return jsonify({'test_storage_id': test_id}), 200
                else:
                    return jsonify({'message': f'Error uploading file to the other endpoint: {response.text}'}), 500
 
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/ai-feedback/lungs-xray', methods=['POST'])
@jwt_required()
def feedback_lungs():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        if (request.method == 'POST'):
            data = request.get_json()
            response = rest.feedback_request(data)
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": "Unknown method type."}), 500
 
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/infer-chat', methods=["GET"])
@jwt_required()
def send_chat_query():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        if (request.method == 'GET'):
            data = request.get_json()
            access_token = request.headers.get('Authorization').replace('Bearer ', '')
            response = rest.nlp_send_query(data, access_token)
            print(response)
            return jsonify({"message" : str(response.json())}), 200
        else:
            return jsonify({"error": "Unknown method type."}), 500
 
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/set-infer-context', methods = ["POST"])
@jwt_required()
def set_inference_context():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        data = request.get_json()
        access_token = request.headers.get('Authorization').replace('Bearer ', '')
        if access_token:
            sched = BackgroundScheduler()
            sched.add_job(auto_inferencing,'interval', minutes = 60, args=[data, current_user])
            sched.start()
            return jsonify({"message":"Scheduler configured successfully"}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def auto_inferencing(tag_data, user):
    with app.app_context():
        try:
            refresh_token = create_refresh_token(user)
            find_new_url = scheme + rest.dicom_ip+':'+str(rest.dicom_port)+'/api/infer-new-data'
            headers = {'Authorization': 'Bearer ' + refresh_token}
            response = requests.get(url = find_new_url, json={"tags":tag_data}, headers=headers)
            if response.status_code == 200:
                success = response.json()["success"]
                failed = response.json()["failed"]
                app.logger.info("Inference Trigger Completed")
                app.logger.info(f"Successful:  {success}")
                app.logger.info(f"Failed: {failed}")
            elif response.status_code == 204:
                app.logger.info("No new data found") 
            else:
                app.logger.info("Internal server error during inference trigger")
        except Exception as e:
            app.logger.info(e)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6000, debug=True)
