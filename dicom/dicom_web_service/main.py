from flask import Flask, request, jsonify, send_file
from utils.utils import DicomwebService
import json
import os
import requests
import shutil
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import yaml
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

config = yaml.safe_load(open('config/auth_config.yaml', 'r'))
service_cfg = json.load(open('config/microservice_conf.json', 'r'))

class DicomConfig:
    def __init__(self):
        self.params = {}

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = config['development']['jwt_secret_key']

ssl_enabled = config['development']['ssl_enabled']
scheme = "http://"
if ssl_enabled:
    scheme = "https://"

jwt = JWTManager(app)
app.logger.setLevel(logging.INFO)

dicom_ip, dicom_port = service_cfg["dicomweb_server"]["ip"], service_cfg["dicomweb_server"]["port"]
cloud_ip, cloud_port = service_cfg["cloud_server"]["ip"], service_cfg["cloud_server"]["port"]
rest_ip, rest_port = service_cfg["rest_server"]["ip"], service_cfg["rest_server"]["port"]

cfg = DicomConfig()

@app.errorhandler(Exception)
def handle_exception(error):
    response = jsonify({"error": str(error)})
    response.status_code = 500  #Internal Server Error
    return response

@app.route('/api/configure', methods = ['POST'])
@jwt_required()
def configure_dicomweb():
    """
    API to configure dicom-service to connect with dicom-web-server
    """
    current_user = get_jwt_identity()
    app.logger.info(f"logged in as:{current_user}")
    dcmweb_config = request.get_json()
    missing_key = []
    for key in ["url", "root", "auth"]:
        if key in dcmweb_config:
            cfg.params[key] = dcmweb_config[key]
        else:
            missing_key.append(key)
            cfg.params[key] = "NA"

    if missing_key:
        return jsonify({"message": "Not enough configuration parameters"}), 400
    else:
        connection_check = dcmweb_ping_server()
        if connection_check[1] == 200:
            return jsonify({'message': 'PACS location added successfully', "verified": True}), 200
        else:
            return jsonify({'message': 'PACS location added successfully', "verified": False}), 201


@app.route('/api/ping', methods=['GET'])
@jwt_required()
def dcmweb_ping_server():
    current_user = get_jwt_identity()
    app.logger.info(f"logged in as:{current_user}")
    url = f"{cfg.params['url']}/{cfg.params['root']}/series"
    auth= (cfg.params['auth'][0],cfg.params['auth'][1]) 
    try:
        response = requests.get(url, auth = auth)
        if response.status_code == 200:
            return {'message': 'DICOMWeb Server Connection Verified'}, 200
        else:
            return {'message': 'Unable to establish connection with DICOMWeb Server'}, 405
    except Exception:
        return {'message': 'DICOMWeb Server not available'}, 404


#API to get study and series details of patient using patientID 
@app.route('/api/query', methods=['GET'])
@jwt_required()
def dcmweb_get_studies():
    current_user = get_jwt_identity()
    app.logger.info(f"logged in as:{current_user}")
    if dcmweb_ping_server()[1] == 200:
        service = DicomwebService()
        series_url = f"{cfg.params['url']}/{cfg.params['root']}/series"
        auth= (cfg.params['auth'][0],cfg.params['auth'][1]) 
        req_body = request.get_json()
        result = service.dicom_web_query(series_url, req_body, auth=auth)
        return jsonify(result['message']), result['status']
    else:
        return {'message': 'DICOMWeb Server not available'}, 404


#API to retrieve data
@app.route('/api/retrieve', methods=['GET'])
@jwt_required()
def retrieve_dicom():
    current_user = get_jwt_identity()
    app.logger.info(f"logged in as:{current_user}")
    service = DicomwebService()
    data = request.get_json()
    dcmweb_url = f"{cfg.params['url']}/{cfg.params['root']}/"
    auth= (cfg.params['auth'][0],cfg.params['auth'][1]) 
    series_uid = data["SeriesInstanceUID"]

    if not data:
        return jsonify({" Message":"Request body is empty"}), 400
    
    if dcmweb_ping_server()[1] == 200:
        response = service.dicom_web_retrieve(data, dcmweb_url, auth)
        if response["status"] == 200:
            if len(response["retrieved_data"]) > 1:
                #If multiple files are present in the series, then only one the first file is downloaded. 
                #Current iDiagnose version can handle only 2D data and hence, only one image is passed as a part of the series. 
                return send_file(response["retrieved_data"][0], as_attachment=True, download_name=f"{series_uid}_download.dcm"), 200
            elif len(response["retrieved_data"]) == 1:
                return send_file(response["retrieved_data"][0], as_attachment=True, download_name=f"{series_uid}_download.dcm"), 200
            else:
                response = {"Message": "No data available for the requested parameters"}, 404
        return jsonify(response)
    else:
        return {'message': 'DICOMWeb Server not available'}, 404


@app.route("/api/examined-training-data", methods=["GET"])
@jwt_required()
def get_dataset_dicomweb():
    current_user = get_jwt_identity()
    app.logger.info(f"logged in as:{current_user}")
    access_token = request.headers.get('Authorization').replace('Bearer ', '')
    services = DicomwebService()
    query_req = request.get_json()
    dicom_query_url = scheme + dicom_ip+':'+str(dicom_port)+'/api/query'
    if access_token is not None:
        headers = {'Authorization': 'Bearer ' + access_token}
        dcm_query_out = requests.get(url = dicom_query_url, json=query_req,headers=headers)
        queries = []
        for patient in dcm_query_out.json():
            for study in patient['studies']:
                for series in study['series']:
                    query_dict = {}
                    query_dict["PatientID"] = patient['PatientID']
                    query_dict["StudyInstanceUID"] = study['study_uid']
                    query_dict["SeriesInstanceUID"] = series['series_uid']       
                    queries.append(query_dict)

        cloud_db_extract_url = scheme + cloud_ip+':'+str(cloud_port)+'/client-api/report/get-patient-records'
        dicom_retrieve_url = scheme + dicom_ip+':'+str(dicom_port)+'/api/retrieve'
    
        db_records_resp = requests.get(url = cloud_db_extract_url,headers=headers)
        if db_records_resp.status_code == 200:
            db_records = db_records_resp.json()["patient_id_record"]
        else:
            return {"message": "Unable to fetch label data from database"}, 400  
        for record in db_records:
            for query in queries:
                if (record["pid"] == query["PatientID"]) and (record["series_uid"]==query["SeriesInstanceUID"]):
                    dcm_retrieve_out = requests.get(dicom_retrieve_url, json=query)
                    if (dcm_retrieve_out.status_code == 200) or (dcm_retrieve_out.status_code == 201):
                        services.create_folder_and_write_file("tmp", record["Inference"], record["series_uid"]+".dcm", dcm_retrieve_out.content)
                    else:
                        return {"message": "DICOM Retrieve failure"}, 400
        shutil.make_archive("train_data", "zip", "tmp")
        return send_file('train_data.zip', as_attachment = True)

@app.route("/api/infer-new-data", methods=["GET"])
@jwt_required(refresh=True)
def infer_new_data():
    current_user = get_jwt_identity()
    app.logger.info("Scheduler trigger from rest interface.")
    app.logger.info(f"logged in as:{current_user}")
    access_token = request.headers.get('Authorization').replace('Bearer ', '')

    service = DicomwebService()
    request_data = request.get_json()
    criteria_tags = request_data["tags"]

    series_url = f"{cfg.params['url']}/{cfg.params['root']}/series"
    auth= (cfg.params['auth'][0],cfg.params['auth'][1]) 
    query_result = service.dicom_web_query(series_url, criteria_tags, auth=auth)

    if query_result["status"] != 200:
        return jsonify(query_result['message']), query_result['status']
    
    current_data = query_result['message']
    current_series = service.separate_series(current_data)

    db_manage_url = scheme + cloud_ip + ":" + str(cloud_port) + '/cloud-api/manage-pacs-studies'
    searchpost_url = scheme + rest_ip + ":" + str(rest_port) + '/api/search'

    if access_token is not None:
        headers = {'Authorization': 'Bearer ' + access_token}
        get_resp = requests.get(db_manage_url, headers = headers)
        if get_resp.status_code == 200:
            existing_series = get_resp.json()['series']
        elif get_resp.status_code == 204:
            post_resp = requests.post(db_manage_url, json = {"series":current_series}, headers=headers)
            if post_resp.status_code == 200:
                app.logger.info("Pushed list of current PACS data to DB. New data received henceforth shall be sent automatically for inferencing")
                return jsonify({"message" : "Collection created"}), 201
            else:
                app.logger.info("Could not update data to DB")
                return jsonify({"message": "Internal Server Error"}), 500
        else:
            return jsonify({"message": "Internal Server Error"}), 500

        if current_series == [] or (sorted(current_series, key=lambda x: str(x)) == sorted(existing_series, key=lambda x: str(x))):
            return jsonify({"message":"No new data available"}), 204
        
        new_series = []
        successful = []
        fail = []
        for patient in current_series:
            if patient not in existing_series:
                app.logger.info(f"Found new series in PACS: {patient}")
                new_series.append(patient)
                request_body = {"PatientID": patient["PatientID"],
                                "series_data": {"StudyInstanceUID":patient["StudyInstanceUID"], 
                                                "SeriesInstanceUID": patient["SeriesInstanceUID"]},
                                "AI_enabled":True}
                app.logger.info("Sending data for inferencing")
                inf_response = requests.post(url = searchpost_url, json=request_body, headers=headers)
                if inf_response.status_code == 200:
                    app.logger.info("Data sent successfully for inferencing")
                    successful.append(patient)
                else:
                    app.logger.info("Unable to send data for inferencing")
                    fail.append(patient)

        resp = requests.post(db_manage_url, json = {"series": new_series}, headers=headers)
        if resp.status_code != 200:
            app.logger.info("Could not update data to DB")
            return jsonify({"message": "Internal Server Error"}), 500
        else:
            return jsonify({"message": "Inference Trigger Completed", "success":successful, "failed":fail}), 200

if __name__ == '__main__':
    app.run(host = "0.0.0.0", port=5001, debug=True)