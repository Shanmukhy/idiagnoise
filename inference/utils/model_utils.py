from zipfile import ZipFile
import time
import requests
import wget
import json
import yaml
from utils.config import Config
 
class ModelChecker:
    def __init__(self, quant_type = "fp32"):
<<<<<<< inference/utils/model_utils.py
        with open('config/auth_config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
        self.access_token = config['development']['access_token']
        cfg = Config('./config/default_model.json','./config/microservice_conf.json')
        self.cloud_ip, self.cloud_port = cfg.get_server_port_ip('cloud_server')
        self.api_url2 = 'http://'+self.cloud_ip+':'+str(self.cloud_port)+'/cloud-api/list/model-info'
=======
        self.api_url = "https://localhost:7000/cloud-api/model/download-link/infer"
        self.api_url2 = "https://localhost:7000/cloud-api/list/model-info"
>>>>>>> inference/utils/model_utils.py
        self.quant_type = quant_type
        self.model = None
 
    def model_checker(self):
        print("Model Listner Started")
        while True:
            self.check_and_load_new_model()
            time.sleep(5*60)
 
    def check_version_id(self):
        headers = {
                "Authorization": "Bearer "+self.access_token,
                "Content-Type": "application/json",
            }
        response_ver = requests.post(self.api_url2,headers=headers)
        latest_timestamp = None
        if response_ver.status_code == 200:
            data = response_ver.json()
            #print(data)
            for nums in data:
                timestamp = nums['timestamp']
                version_id = nums['train_id']
                timestamp_float = timestamp[8:]
                # Check if the current timestamp is the latest
                if latest_timestamp is None or timestamp_float > latest_timestamp:
                    latest_timestamp = timestamp
                    latest_version_id = version_id
        return latest_version_id
 
 
    def check_and_load_new_model(self):
        try:
            version_id = self.check_version_id()
            self.api_url = 'http://'+self.cloud_ip+':'+str(self.cloud_port)+"/cloud-api/model/"+version_id+"/download-link"
            headers = {
                "Authorization": "Bearer "+self.access_token,
                "Content-Type": "application/json",
            }
            response = requests.post(self.api_url, json={"version_id":version_id},headers=headers)
 
            if response.status_code == 200:       
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    url = response.json().get('url', None)
                    print(f"Download URL: {url}")
                else:
                    print(response.text)
            elif response.status_code == 404:
                raise FileNotFoundError("RestAPI endpoint not found.")
            else:
                return None
            
            latest_model_path = wget.download(url)
            print(latest_model_path)
            
 
            with ZipFile(latest_model_path, "r") as zip_ref:
                zip_ref.extractall("./model")
            
            print("New Model is available.")
        
        except Exception as e:
            print(f"Error checking or loading model: {e}")


    
    