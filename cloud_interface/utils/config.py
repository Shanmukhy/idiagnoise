import json

class config:
    def __init__(self):
        config_file_path = 'config/azure_credentials.json'
        with open(config_file_path, 'r') as config_file:                
            data = json.load(config_file)
        report_data = data["report_blob"]
        train_data= data["training_data_blob"]
        model_data=data["model_blob"]
        dcmimage_data=data["dcmimage_blob"]
        self.account_name = report_data['account_name']
        self.account_key = report_data['account_key']
        self.report_container = report_data['container_name']
        self.blob_endpoint = report_data['blob_service_endpoint']
        self.train_container = train_data['container_name']
        self.model_container = model_data['container_name']
        self.dcmimage_container = dcmimage_data['container_name']