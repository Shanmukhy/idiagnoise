from zipfile import ZipFile
import time
import requests
import wget
import os
import yaml
from utils.config import Config


class ModelDownloader:
    def __init__(self, quant_type, version_id="latest"):
        with open('config/auth_config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
        self.access_token = config['development']['access_token']
        cfg = Config('./config/default_model.json','./config/microservice_conf.json')
        self.cloud_ip, self.cloud_port = cfg.get_server_port_ip('cloud_server')
        self.api_url = 'http://'+self.cloud_ip+':'+str(self.cloud_port)+"/cloud-api/model/"+version_id+"/download-link"
        self.api_url2 = 'http://'+self.cloud_ip+':'+str(self.cloud_port)+'/cloud-api/list/model-info'
        self.quant_type = quant_type
        self.model = None
        self.version_id = version_id
        self.download_url = None

    def check_latest_version_id(self):
        headers = {
                "Authorization": "Bearer "+self.access_token,
                "Content-Type": "application/json",
            }
        response_ver = requests.post(self.api_url2,headers=headers)
        latest_timestamp = None
        latest_version_id = None
        if response_ver.status_code == 200:
            data = response_ver.json()
            #print(data)
            for nums in data:
                timestamp = nums['timestamp']
                version_id = nums['model_id']
                model_name = nums['model_name']
                timestamp_float = timestamp[8:] 
                # Check if the current timestamp is the latest
                if latest_timestamp is None or timestamp_float > latest_timestamp:
                    latest_timestamp = timestamp
                    latest_version_id = version_id
        return latest_version_id

    
    def download_and_extract_model(self, url):
        try:
            # Download the model zip file
            print(url)
            latest_model_path = wget.download(url)
            # print(latest_model_path)

            # Extract the model to the 'model' directory
            with ZipFile(latest_model_path, "r") as zip_ref:
                zip_ref.extractall("./model")      
        except Exception as e:
            print(f"Error checking or loading model: {e}")
    
    def get_download_url(self):
        try:
            version_id = self.version_id
            if "latest" in self.version_id.lower():
                version_id = self.check_latest_version_id()

            if version_id is None:
                raise ValueError("Invalid model id provided.")
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
            return url
        except Exception as e:
            print(f"Error checking or loading model: {e}")


    def list_available_models(self):
        try:
            headers = {
                "Authorization": "Bearer "+self.access_token,
                "Content-Type": "application/json",
            }
            response = requests.post(self.api_url2,headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                available_models = [model['model_name'] for model in data]
                print("Available Models:")
                for model_id in available_models:
                    print(f"- {model_id}")
                return available_models
            else:
                print(f"Failed to retrieve available models. Status code: {response.status_code}")
                return []

        except Exception as e:
            print(f"Error listing available models: {e}")
            return []

   
    def is_valid_model_id(self, model_id):
        try:
            available_models = self.list_available_models()

            if len(model_id) == 15 and model_id in available_models:
                print(f"The model ID '{model_id}' is valid.")
                return True
            else:
                print(f"The model ID '{model_id}' is not valid. Please choose a 15-character ID from the available models.")
                return False
        except Exception as e:
            print(f"Error validating model ID: {e}")
            return False

class TestDataDownloader:
    def __init__(self):
        self.download_url = None
        with open('config/auth_config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
        self.access_token = config['development']['access_token']
        cfg = Config('./config/default_model.json','./config/microservice_conf.json')
        self.cloud_ip, self.cloud_port = cfg.get_server_port_ip('cloud_server')

    def get_testdata_url(self,test_storage_id):
        try:
            cloud_url = 'http://'+self.cloud_ip+':'+str(self.cloud_port)+"/cloud-api/test-data/"+test_storage_id+"/download"
            headers = {
                "Authorization": "Bearer "+self.access_token,
                "Content-Type": "application/json",
            }
            response=requests.post(cloud_url,headers=headers)
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
            return url
        except Exception as e:
            print(f"Error checking or loading model: {e}")

    def download_data(self,test_id):
        try:
            url=self.get_testdata_url(test_id)
            file_name = wget.download(url)
            # Get the relative path of the downloaded file
            current_directory = os.getcwd()
            relative_path = os.path.relpath(file_name, current_directory)

            return relative_path

        except Exception as e:
            print(f"Error downloading data: {e}")
            return None
    
    def extract_file(self,test_id):
        testdata_path=self.download_data(test_id)
        test_zip = os.path.basename(testdata_path)
        extract_directory = "./test_data"
        with ZipFile(test_zip, "r") as zip_ref:
                zip_ref.extractall(extract_directory)
        return extract_directory 
        


