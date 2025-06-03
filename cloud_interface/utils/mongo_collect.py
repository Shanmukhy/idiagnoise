from pymongo import MongoClient
from cloud.api import CloudInterface
from cloud.test_api import TestDataStorage
from flask import jsonify
from utils.config import config

config_instance=config()
cloud_interface_instance = CloudInterface() 
test_instance=TestDataStorage()

class  MongoCollection:
    def __init__(self):
        self.mongo_uri = "mongodb://localhost:27017/"
        self.database_name = "local"
        self.collection_name_train = "Train_data"
        self.collection_name_test='Test_data'
        self.collection_name_model='ModelDB'
        self.collection_name_reports = "Patients"
        self.collection_name_dicomstudies = "Dicom_studies"
        self.mongo_client = MongoClient(self.mongo_uri)
        self.mongo_db = self.mongo_client[self.database_name]
        self.train_mongo_collection = self.mongo_db[self.collection_name_train]
        self.test_mongo_collection=self.mongo_db[self.collection_name_test]
        self.model_mongo_collection=self.mongo_db[self.collection_name_model]
        self.report_mongo_collection=self.mongo_db[self.collection_name_reports]
        self.dicomstudies_mongo_collection=self.mongo_db[self.collection_name_dicomstudies]
    
    def Train_data_DB_update(self, train_id, blob_url, blob_name,timestamp):
        try:
            
            train_data_info = {
                "train_id": train_id,
                "Blob_URL": blob_url,
                "Blob_name": blob_name,
                "timestamp":timestamp
            }        
            result = self.train_mongo_collection.insert_one(train_data_info)        
            return result.inserted_id

        except Exception as e:
            return print("Error in updating the Mongodb")
        
    def Test_data_DB_update(self,test_storage_id,blob_url,blob_name,timestamp_str):
        try:
            test_data_info = {
                "test_id": test_storage_id,
                "Blob_URL": blob_url,
                "Blob_name": blob_name,
                "timestamp":timestamp_str
                    }
            result = self.test_mongo_collection.insert_one(test_data_info)
            return result.inserted_id
        except Exception as e:
            return print("Error in updating the mongodb")
        
    def download_link(self,version_id):
        model_info = self.model_mongo_collection.find_one({"version_id": version_id})
        if model_info:
            blob_name = model_info.get("model_name", "Model_name")
            download_url = cloud_interface_instance.create_SAS_token(blob_name,config_instance.model_container,duration=30)
        return download_url
    
    def get_model_info(self):
        field_name = "verion_id"
        list_version_ids = self.model_mongo_collection.find({}, {field_name: 1, 'model_name': 1, 'timestamp': 1, '_id': 0})
        version_ids = [{"version_id": doc[field_name], "model_name": doc.get('model_name', ''), "timestamp": doc.get('timestamp', '')} for doc in list_version_ids]
        return version_ids 
    
    def get_patient_records(self):
        check_isfalsepositive = self.report_mongo_collection.find_one({'is_false_positive': True})

        if check_isfalsepositive:
            cursor = self.report_mongo_collection.find({})
            patient_records = [str(document['_id']) for document in cursor]

        return patient_records
        
    def build_dicom_return_json(self, data):
        pdf_location = cloud_interface_instance.create_SAS_token(data['Blobname'],config_instance.report_container, 30)
        pid = data['Patient_ID']
        ai = data['Inference']
        
        return_body = {
            "PatientID": pid,
            "ReportLink": pdf_location,
            "AI_Result": ai
        }
        
        return return_body

    def update_record(self, patient_id, series_id, inference_results, report_blob_name, image_blob_name):
        query = {"Patient_ID": patient_id, "SeriesUID": series_id}
        update = {"$set": {"Inference": inference_results, "Blobname": report_blob_name, "ImageStoragePath": image_blob_name}}
        result = self.report_mongo_collection.update_one(query, update, upsert=True)
        patient_data = self.report_mongo_collection.find_one(query)
        return_data = self.build_dicom_return_json(patient_data)
        return return_data
    
    def get_test_url(self,test_id):
        test_info = self.test_mongo_collection.find_one({"test_id": test_id})
        if test_info:
            blob_name = test_info.get("Blob_name", "Blob_name")
            download_url = cloud_interface_instance.create_SAS_token(blob_name,config_instance.train_container,duration=30)

        return download_url
    
    def delete_record(self, data):
        train_info = self.train_mongo_collection.find_one({"train_id": data['train_id']})
        test_info = self.test_mongo_collection.find_one({"test_id": data['test_id']})
        model_info = self.model_mongo_collection.find_one({"version_id": data['version_id']})

        if train_info:
            blob_name = train_info.get("Blob_name", "Blob_name")
            cloud_interface_instance.delete_blob(config_instance.train_container, blob_name)
            self.train_mongo_collection.delete_one({"train_id": data['train_id']})

        if test_info:
            blob_name = test_info.get("Blob_name", "Blob_name")
            cloud_interface_instance.delete_blob(config_instance.train_container, blob_name)
            self.test_mongo_collection.delete_one({"test_id": data['test_id']})

        if model_info:
            model_name = model_info.get("Model_name", "Model_name")
            cloud_interface_instance.delete_blob(config_instance.model_container, model_name)
            self.model_mongo_collection.delete_one({"version_id": data['version_id']})
        print("Successfully deleted the record")

    def post_feedback(self, patient_id, series_uid, user_inference):
        criteria = {'Patient_ID': patient_id, 'SeriesUID': series_uid}
        matched_document = self.report_mongo_collection.find_one(criteria)

        if matched_document:
            self.report_mongo_collection.update_one(criteria, {"$set": {"User Inference": user_inference}})
            if matched_document["Inference"] == user_inference:
                self.report_mongo_collection.update_one(criteria, {"$set": {"is_false_positive": False}})
            else:
                self.report_mongo_collection.update_one(criteria, {"$set": {"is_false_positive": True}})
            return jsonify({"message": "Feedback Stored Successfully"}), 200
        else:
            return jsonify({"error": "No document found matching the criteria."}), 404

    def search_db_record(self, patient_id, series_uid):
        criteria = {'Patient_ID': patient_id, 'SeriesUID': series_uid}
        matched_document = self.report_mongo_collection.find_one(criteria)
        if matched_document:
            if "User Inference" in matched_document and matched_document["User Inference"]:
                inference_val = matched_document["User Inference"]
            else:
                inference_val = matched_document["Inference"]
            image_path = matched_document["ImageStoragePath"]
            download_url = cloud_interface_instance.create_SAS_token(image_path,config_instance.dcmimage_container,duration=30)
            return jsonify({"inference": inference_val, "image_path": download_url})
        
        else:
            return None
        
    def get_dicom_study_list(self):
        full_cursor = self.dicomstudies_mongo_collection.find({}, {"_id":0})
        existing_studies = list(full_cursor)
        return existing_studies
