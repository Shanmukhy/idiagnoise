from flask import Flask, request, jsonify, send_file
from pynetdicom import AE
from pynetdicom.sop_class import Verification
import requests
import json
from utils.utils import DicomService
import shutil
import yaml
import logging
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity


config = yaml.safe_load(open('config/auth_config.yaml', 'r'))
service_cfg = json.load(open('config/microservice_conf.json', 'r'))

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = config['development']['jwt_secret_key']

class DicomConfig:
    def __init__(self):
        self.params = {}

ssl_enabled = config['development']['ssl_enabled']
scheme = "http://"
if ssl_enabled:
    scheme = "https://"

jwt = JWTManager(app)
app.logger.setLevel(logging.INFO)

dicom_ip, dicom_port = service_cfg["dicom_server"]["ip"], service_cfg["dicom_server"]["port"]
cloud_ip, cloud_port = service_cfg["cloud_server"]["ip"], service_cfg["cloud_server"]["port"]
rest_ip, rest_port = service_cfg["rest_server"]["ip"], service_cfg["rest_server"]["port"]
cfg = DicomConfig()

@app.errorhandler(Exception)
def handle_exception(error):
    #Handles exceptions to provide error messages without breaking
    response = jsonify({"error": str(error)})
    response.status_code = 500  #Internal Server Error
    return response


@app.route('/api/configure', methods = ['POST'])
@jwt_required()
def configure_pacs():
    """
    API to configure dicom-service to connect with PACS
    """
    current_user = get_jwt_identity()
    app.logger.info(f"logged in as:{current_user}")
    pacs_config = request.get_json()
    missing_key = []
    for key in ["address", "port", "ae_title"]:
        if key in pacs_config:
            cfg.params[key] = pacs_config[key]
        else:
            missing_key.append(key)
            cfg.params[key] = pacs_config[key]

    if missing_key:
        return jsonify({"message": "Not enough configuration parameters"}), 400
    else:
        connection_check = echo_pacs()
        if connection_check[1] == 200:
            return jsonify({'message': 'PACS location added successfully', "verified": True}), 200
        else:
            return jsonify({'message': 'PACS location added successfully', "verified": False}), 201


@app.route('/api/echo', methods=['GET'])    #Get API to verify connectivity with DICOM Server
@jwt_required()
def echo_pacs():
    """
    API to verify connection with PACS
    """
    # Create DICOM Association
    current_user = get_jwt_identity()
    app.logger.info(f"logged in as:{current_user}")
    ae = AE(ae_title=b'iDiagnose')
    ae.add_requested_context(Verification)
    assoc = ae.associate(cfg.params["address"], cfg.params['port'], ae_title=cfg.params['ae_title'])

    #Send C-Echo Request to DICOM server
    if assoc.is_established:
        status = assoc.send_c_echo()
        if status.Status == 0:
            assoc.release()
            return jsonify({'message': 'C-ECHO successful'}), 200  #C-Echo Success response
        else:
            return jsonify({'message': 'C-ECHO failure'}), 400   #C-Echo Failure response
    else:
        return jsonify({'message': 'Failed to establish association with PACS server'}), 404   #Association Failure reponse


@app.route('/api/query', methods=['GET'])
@jwt_required()
def query_pacs():
    """"
    API to query medical image data from PACS
    """
    current_user = get_jwt_identity()
    app.logger.info(f"logged in as:{current_user}")
    services = DicomService()
    req_body = request.get_json()
    ds = services.create_ds_from_request_body(req_body)
    results = services.c_find_pacs(ds, cfg.params['address'], cfg.params['port'])
    return jsonify(results['message']), results['status']


@app.route("/api/retrieve", methods=["GET"])
@jwt_required()
def retrieve_data():
    current_user = get_jwt_identity()
    app.logger.info(f"logged in as:{current_user}")
    services = DicomService()
    request_data = request.json
    
    ds = services.create_ds_from_request_body(request_data)
    response_data = services.c_get_pacs(ds, hostname=cfg.params['address'], port=cfg.params['port'])
    if response_data['status'] == 200:
        if len(response_data["retrieved_data"]) == 1:
            print("Sending Data")
            return send_file(response_data["retrieved_data"][0], as_attachment=True, download_name=f"{ds.SeriesInstanceUID}_download.dcm"), 200
        else:
            #If multiple files are present in the series, then only one the first file is downloaded. 
            #This current version of iDiagnose can handle only 2D data and hence, only one image is passed as a part of the series.                
            return send_file(response_data["retrieved_data"][0], as_attachment=True, download_name=f"{ds.SeriesInstanceUID}_download.dcm"), 200              
    else:
        return jsonify({'message':response_data['message']}), response_data['status']


@app.route("/api/examined-training-data", methods=["GET"])
@jwt_required()
def get_dataset_pacs():
    current_user = get_jwt_identity()
    app.logger.info(f"logged in as:{current_user}")
    access_token = request.headers.get('Authorization').replace('Bearer ', '')
    services = DicomService()
    query_req = request.get_json()
    dicom_query_url = scheme + dicom_ip+':'+str(dicom_port)+'/api/query'
    if access_token is not None:
        headers = {'Authorization': 'Bearer ' + access_token}
        dcm_query_out = requests.get(url = dicom_query_url, json=query_req, headers=headers)
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
            db_records = db_records_resp.json()["patient_records"]
        else:
            return {"message": "Unable to fetch label data from database"}, 400  
        for record in db_records:
            for query in queries:
                if (record["pid"] == query["PatientID"]) and (record["series_uid"]==query["SeriesInstanceUID"]):
                    dcm_retrieve_out = requests.get(dicom_retrieve_url, json=query, headers= headers)
                    if (dcm_retrieve_out.status_code == 200):
                        services.create_folder_and_write_file("tmp", record["Inference"], record["series_uid"]+".dcm", dcm_retrieve_out.content)
                    else:
                        return {"message": "DICOM Retrieve failure"}, 400
        shutil.make_archive("train_data", "zip", "tmp")
        return send_file('train_data.zip', as_attachment = True), 200

@app.route("/api/infer-new-data", methods=["GET"])
@jwt_required(refresh=True)
def infer_new_data():
    current_user = get_jwt_identity()
    app.logger.info("Scheduler trigger from rest interface.")
    app.logger.info(f"logged in as:{current_user}")
    access_token = request.headers.get('Authorization').replace('Bearer ', '')

    services = DicomService()
    request_data = request.get_json()
    criteria_tags = request_data["tags"]
    ds = services.create_ds_from_request_body(criteria_tags)
    c_find_resp = services.c_find_pacs(ds, hostname=cfg.params['address'], port=cfg.params['port'])

    if c_find_resp["status"] != 200:
        return jsonify(c_find_resp['message']), c_find_resp['status']
    
    current_data = c_find_resp['message']
    current_series = services.separate_series(current_data)

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

        if current_series==[] or (sorted(current_series, key=lambda x: str(x)) == sorted(existing_series, key=lambda x: str(x))):
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
    app.run(host="0.0.0.0", port= 5000, debug = True)
	