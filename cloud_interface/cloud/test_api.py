from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient,ContentSettings
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from datetime import datetime,timedelta
from utils.config import config

config_instance=config()

class TestDataStorage:
    def __init__(self):
        pass
    
    def upload_blob(self,cont_name,filename,file_data):
        blob_service_client = BlobServiceClient(account_url=config_instance.blob_endpoint, credential=config_instance.account_key)
        container_client = blob_service_client.get_container_client(cont_name)
        container_client.upload_blob(name=filename, data=file_data, content_settings=ContentSettings(content_type='application/zip'))
        blob_client = container_client.get_blob_client(filename)
        blob_url = blob_client.url
        print("successfully uploaded data to cloud")
        return blob_url
    
    def generate_name(self,prefix='test_data'):
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
        blob_name = f'{prefix}_{timestamp_str}.zip'
        id = f'{prefix}_{timestamp_str}'
        return blob_name, id,timestamp_str