from flask import Flask, request, jsonify, send_file
import base64
import numpy as np
import tensorflow as tf
from model.prepost import PrePost
import traceback
from pymongo import MongoClient
from utils.model_utils import ModelChecker
from model.downloader import ModelDownloader,TestDataDownloader
from model.test import TestModel
from model.compile import TFTRTCompile
import threading
import argparse
import shutil
import os
from utils.config import Config
import yaml
import logging
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

def parse_args():
    parser = argparse.ArgumentParser(description="Inference model on Lungs Xray dataset.")
    parser.add_argument("--img_height", type=int, default=224, help="Height of the input images")
    parser.add_argument("--img_width", type=int, default=224, help="Width of the input images")
    parser.add_argument("--model", type=str, default="custom", required=True, help="Provide the model name, from list: [resnet50, mobilenet, mobilenetv2, vgg16, vgg19, xception, custom]")
    parser.add_argument("--model_id", type=str, default="latest", help="Perform model download provided model version.")
    parser.add_argument("--test_data_id", type=str, default=None, help="Load the testing dataset as per testing id or latest.")
    parser.add_argument('--quantize_type', type=str, default=None, choices=['fp16','fp32','int8'], help='Quantization type')
    return parser.parse_args()

class_list = ['Consolidation', 'Mass', 'Infiltration', 'No_Finding', 'Hernia', 'Pneumonia', 'Effusion', 'Edema', 'Pleural_Thickening', 'Emphysema', 'Atelectasis', 'Nodule', 'Fibrosis', 'Cardiomegaly', 'Pneumothorax']
app = Flask(__name__)
with open('config/auth_config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)
app.config['JWT_SECRET_KEY'] = config['development']['jwt_secret_key']
jwt = JWTManager(app)
app.logger.setLevel(logging.INFO)
t = None # Tester Object
pr = None # Preprocessor Object
trt = None # Compiler Object
args = parse_args()

@app.route('/api/infer/lungs-xray', methods=['POST'])
@jwt_required()
def infer_xray():
    ''' Return the dummy data of the patient. '''
    try:
        current_user = get_jwt_identity()
        app.logger.info(f"logged in as:{current_user}")
        file = request.get_json()['patient_dicom'][2:-1] ## byte file
        dtype = request.get_json()['dtype']
        input = pr.img_proc(file, dtype)
        result = trt.predictor(input)
        res = pr.get_argmax_res(result)

        if os.path.exists("./model"):
            trt = TFTRTCompile('./model', args.quantize_type)
            trt.compile()
            trt.build(t.get_val_data(32))
            print("Loaded new model.")

            shutil.rmtree('./model')
            print("Removed the loaded model")

        return jsonify({'ai_result':class_list[res]})
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        return jsonify({'message': 'ERROR WITH INFERENCE'}), 404

if __name__ == '__main__':


    cfg = Config('./config/default_model.json','./config/microservice_conf.json')
    args.model_id = cfg.get_version_id()

    md = ModelDownloader(args.quantize_type, args.model_id)
    download_url = md.get_download_url()
    md.download_and_extract_model(download_url)

    if md.is_valid_model_id(args.model_id == False):
        raise ValueError("Invalid model id.")

    t = TestModel()
    pr = PrePost()
    td= TestDataDownloader()

    if args.test_data_id is not None:
        test_data=td.extract_file(args.test_data_id)
        trt = TFTRTCompile('./model', args.quantize_type)
        trt.compile()
        trt.build(t.get_val_data(32,test_data))
        score = t.test('./model')
        print("Model Accuracy:", score)
        
    else:
        OUTPUT_SAVED_MODEL_DIR = "./saved_model"

        trt = TFTRTCompile('./model', args.quantize_type)
        trt.compile()
        data='./test_data/'
        trt.build(t.get_val_data(32,data))

        print("Loaded model.")

        shutil.rmtree('./model')
        print("Removed the loaded model")


    mc = ModelChecker()
    thread = threading.Thread(target=mc.model_checker)
    thread.start()


    app.run(host="0.0.0.0", port=7000, debug=False)
