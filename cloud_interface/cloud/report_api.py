from azure.storage.blob import BlobServiceClient
from datetime import datetime,timedelta
from utils.config import config

config_instance=config()

class ReportMaintainanceStorage:
    def upload_b64_to_cloud(self, b64_data, filename, type):
        if type == "image":
            container = config_instance.dcmimage_container
        elif type == "report":
            container = config_instance.report_container
        else:
            raise ValueError("Invalid data type")
        
        blob_service_client = BlobServiceClient(account_url=config_instance.blob_endpoint, credential=config_instance.account_key)
        container_client = blob_service_client.get_container_client(container)

        print(f"Uploading blob: {filename}")
        if container_client.get_blob_client(filename).exists():
            print(f"The blob '{filename}' already exists. Updating the existing blob.")
            container_client.get_blob_client(filename).delete_blob()
        
        try:
            container_client.upload_blob(data=b64_data, name=filename)
            return True
        except Exception as e:
            print("Error occured while uplaoding blob: ", str(e))
            return False
