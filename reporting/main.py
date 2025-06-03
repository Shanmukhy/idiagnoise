from flask import Flask, request, jsonify
from utils.utils import ReportGeneration, SrUtils,GenAIChatBot
import base64
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import yaml
import logging

app = Flask(__name__)
with open('config/auth_config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)
app.config['JWT_SECRET_KEY'] = config['development']['jwt_secret_key']
jwt = JWTManager(app)
app.logger.setLevel(logging.INFO)
report_generator = ReportGeneration()
result_list=[]


@app.route('/api/create-interim-report', methods=['GET'])
@jwt_required()
def generate_report():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        dicom_data = request.files['dicom_data'].read()
        inference = request.form['inference']
        dicom_info = report_generator.extract_dicom_info(dicom_data)
        patient_id = dicom_info['PatientID']
        series_id = dicom_info['SeriesInstanceUID']
        report_data= report_generator.generate_report(inference, dicom_data)
        with open(report_data, "rb") as file:
            pdf_bytes = file.read()
        encoded_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        return jsonify({"file": encoded_pdf, "PatientID": patient_id, "SeriesInstanceUID": series_id}), 200
        
    except Exception as e:
        return jsonify({"Error": str(e)}), 500
    
@app.route('/api/create-dicom-sr', methods=['GET'])
@jwt_required()
def create_dicom_structured_report():
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        dicom_data = request.files['dicom_data'].read()
        inference = eval(request.form["inference"])
        sr_utils = SrUtils()
        dicom_sr_ds = sr_utils.create_dicom_sr(inference, dicom_data)
        b64_dcm = sr_utils.dicom_ds_to_b64(dicom_sr_ds).decode("utf-8")
        return jsonify({"file": b64_dcm, "PatientID": sr_utils.patient_id, "SeriesInstanceUID": sr_utils.series_uid}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/handle-query', methods=['GET'])
@jwt_required()
def handle_query():
    print(request.get_json())
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        data = request.get_json()
        if 'query' in data and 'conditions' in data:
            gen_ai_chatbot = GenAIChatBot(data["conditions"])
            user_input = data.get('query')
            result = gen_ai_chatbot.handle_query(user_input)
            inference = data.get("inference")
            if result != "Insufficient data":
                keyword = result
                result_inference = gen_ai_chatbot.query_inference_result(keyword, inference)
                return jsonify({"response":str(result_inference)}), 200
            else:
                return jsonify({"error": "Insufficient data"}), 400
        else:
            return jsonify({"error": "Invalid input data"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port = 5010, debug = True)