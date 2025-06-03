from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime,timedelta
from utils.config import config

config_instance=config()

class CloudInterface:
    def __init__(self):
        pass
    
    def create_SAS_token(self,blob_name,container_name,duration=30): 
        
        start_time = datetime.utcnow()
        expiry_time = start_time + timedelta(minutes=duration)  

        sas_permissions = BlobSasPermissions(read=True, write=False, delete=False, list=True)

        # Generate the SAS token
        sas_token = generate_blob_sas(account_name=config_instance.account_name,
                               container_name=container_name,
                               blob_name=blob_name,
                               account_key=config_instance.account_key,
                               permission=sas_permissions,
                               expiry=expiry_time)

        sas_url = f"https://{config_instance.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        
        return sas_url
    
    def download_latest(self,cont_name):
        blob_service_client = BlobServiceClient(account_url=config_instance.blob_endpoint, credential=config_instance.account_key)
        container_client = blob_service_client.get_container_client(cont_name) 
        blob_list = container_client.list_blobs()
        latest_blob = max(blob_list, key=lambda x: x.last_modified)
        blob_name = latest_blob.name 
        latest_url = self.create_SAS_token(blob_name,cont_name,duration=30)
        return latest_url
    
    def delete_blob(self,cont_name,blob_name):
        blob_service_client = BlobServiceClient(account_url=config_instance.blob_endpoint, credential=config_instance.account_key)
        blob_client = blob_service_client.get_blob_client(container=cont_name, blob=blob_name)
        blob_client.delete_blob()
        print("blob deleted successfully")
    
    
    
    
    