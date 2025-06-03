from pymongo import MongoClient
from utils.config import Config
from model.model_utils import ModelMeta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from zipfile import ZipFile
import wget
from azure.storage.blob import BlobServiceClient
from datetime import datetime, timedelta

class ModelCollection:
    def __init__(self, mongo_server):
        self.mongo_uri = mongo_server["mongo_uri"]
        self.database_name = mongo_server["database_name"]
        self.collection_name = "ModelDB"
        self.cfg = Config("config/config.json")
        self.model_meta = ModelMeta()

        self.mongo_client = MongoClient(self.mongo_uri)
        self.mongo_db = self.mongo_client[self.database_name]
        self.mongo_collection = self.mongo_db[self.collection_name]

        azure_blob_credentials = self.cfg.read_config(config_key="model_blob")

        # Azure Blob configuration
        self.account_name = azure_blob_credentials.get("account_name", "")
        self.account_key = azure_blob_credentials.get("account_key", "")
        self.container_name = azure_blob_credentials.get("container_name", "")
        self.blob_service_endpoint = azure_blob_credentials.get("blob_service_endpoint", "")

    def create_SAS_token(self,blob_name,duration=30):
        
        start_time = datetime.utcnow()
        expiry_time = start_time + timedelta(minutes=duration)  
 
        sas_permissions = BlobSasPermissions(read=True, write=False, delete=False, list=True)
        
 
        # Generate the SAS token
        sas_token = generate_blob_sas(account_name=self.account_name,
                               container_name=self.container_name,
                               blob_name=blob_name,
                               account_key=self.account_key,
                               permission=sas_permissions,
                               expiry=expiry_time)
 
        sas_url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"
        # print(sas_url)
        return sas_url

    def download_model(self, model_path, backbone_name, version_id):
        if version_id != '':
            model_info = self.mongo_collection.find_one({"model_ver": version_id, "backbone": backbone_name})
            if model_info:
                blob_name = model_info['model_name']
                
                download_url = self.create_SAS_token(blob_name)

                wget.download(download_url)
                
                print(f"Model downloaded to: {blob_name}")

                zf = ZipFile(blob_name)
                zf.extractall(model_path)
    
                return model_path

    
    def upload_model(self, model_path, backbone_name, version_id):
        # Create BlobServiceClient
        blob_service_client = BlobServiceClient(account_url=self.blob_service_endpoint, credential=self.account_key)

        # Create a ContainerClient
        container_client = blob_service_client.get_container_client(self.container_name)

        # Upload the TFTRT file to Azure Blob Storage and overwrite the existing blob
        with open(model_path, "rb") as data:
            # container_client.upload_blob(name=unique_blob_name, data=data, overwrite=True)
            container_client.upload_blob(name=model_path, data=data, overwrite=True)

        blob_endpoint = f"{self.blob_service_endpoint}/{self.container_name}/{model_path}"

        print(f"TFTRT file uploaded to Azure Blob Storage. Blob URL: {blob_endpoint}")

        # # Get metadata of the TFTRT file
        blob_client = container_client.get_blob_client(blob=model_path)
        tf_trt_metadata = blob_client.get_blob_properties()

        # Print metadata
        print("TFTRT model metadata:")
        print(tf_trt_metadata)
        # print("Blob URL:", blob_service_endpoint + "/" + container_name + "/" + unique_blob_name)
        print("Blob URL:", self.blob_service_endpoint + "/" + self.container_name + "/" + model_path)
        current_time = self.model_meta.generate_current_datetime()
        try:
            # Check if the patient ID already exists
            model_data = self.mongo_collection.find_one({"model_ver": version_id})
            
            if model_data:
                print("Model record already exist.")
                return False
            else:
                # Insert new record
                model_obj = {"model_ver": version_id, "model_name": model_path, "blob_endpoint": blob_endpoint, "backbone" : backbone_name, "time":current_time}
                
                self.mongo_collection.insert_one(model_obj)
                print("Record Saved: ", model_obj)
                return True
    
        except Exception as e:
            print("Error: ", e)
