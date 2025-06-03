import os
import tensorflow as tf
from azure.storage.blob import BlobServiceClient
from zipfile import ZipFile
import shutil
from pymongo import MongoClient
import numpy as np


class Dataset:
    def __init__(self, data_dir, img_h, img_w, mongo_server):
        self.data_dir = data_dir

        self.img_h = img_h
        self.img_w = img_w
        
        self.mongo_uri = mongo_server['mongo_uri']
        self.database_name = mongo_server["database_name"]
        self.collection_name = "TrainingDB"

        self.mongo_client = MongoClient(self.mongo_uri)
        self.mongo_db = self.mongo_client[self.database_name]
        self.mongo_collection = self.mongo_db[self.collection_name]
        # Initialize train_datagen in the constructor
        self.get_augment_generator()

    def histogram_stretching(self, image):
        min_intensity, max_intensity = np.min(image), np.max(image)
        stretched_image = np.clip((image - min_intensity) / (max_intensity - min_intensity) * 255, 0, 255)
        return stretched_image

    def get_augment_generator(self):
        self.train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
            preprocessing_function=self.histogram_stretching,
            rotation_range=10, # rotation
            width_shift_range=0.2, # horizontal shift
            height_shift_range=0.2, # vertical shift
            zoom_range=0.2, # zoom
            horizontal_flip=True, # horizontal flip
            brightness_range=([0.2,1.2]), # brightness
            fill_mode='nearest', # fill any empty pixels with the nearest value
            shear_range=0.2 #apply random shear transformations
        )

        return self.train_datagen

    def get_augmented_train_data(self, batch_size):
        train_ds = self.train_datagen.flow_from_directory(
            self.data_dir,
            subset="training",
            seed=123,
            target_size=(self.img_h, self.img_w),
            batch_size=batch_size,
            class_mode='categorical'
        )

        return train_ds


    def get_augmented_val_data(self, batch_size):
        val_ds = self.train_datagen.flow_from_directory(
            self.data_dir,
            subset="validation",
            seed=123,
            target_size=(self.img_h, self.img_w),
            batch_size=batch_size,
            class_mode='categorical'
        )

        return val_ds

    def preprocess_data(self, image, label):
        label = tf.one_hot(label, self.CLASSES_LEN)  
        return image, label
    
    def get_train_data(self, batch_size):
        # Training Subset
        train_ds = tf.keras.preprocessing.image_dataset_from_directory(
            self.data_dir,
            validation_split=0.2,
            subset="training",
            seed=123,
            image_size=(self.img_h, self.img_w),
            batch_size=batch_size
        )
        # DIAG-311 Creation of batches of images as per batch_size from configuration
        train_ds = train_ds.map(self.preprocess_data)
        return train_ds
    
    def get_val_data(self, batch_size):
         # Validation dataset
        val_ds = tf.keras.preprocessing.image_dataset_from_directory(
            self.data_dir,
            validation_split=0.2,
            subset="validation",
            seed=123,
            image_size=(self.img_h, self.img_w),
            batch_size=batch_size
        )

        val_ds = val_ds.map(self.preprocess_data)
        return val_ds
    
    def download_from_cloud(self, training_blob_cred, csp, train_data_id):
        # Check if the patient ID already exists
        model_data = self.mongo_collection.find_one({"train_id": train_data_id})
        if model_data:
            downloaded_blob_name = model_data['Blob_name']
        elif train_data_id == None:
            downloaded_blob_name = "train_data.zip"
        else:
            raise FileNotFoundError
        
        # training_blob_cred = cfg.read_config(config_key="training_data_blob")
        if csp.lower() == "azure":
            account_name = training_blob_cred['account_name'] # storage account name
            account_key = training_blob_cred['account_key'] # storage account key
            container_name = training_blob_cred['container_name']  # contrainer name
            blob_service_endpoint = training_blob_cred['blob_service_endpoint'] # server endpoint name

            # Create a BlobServiceClient
            blob_service_client = BlobServiceClient(account_url=blob_service_endpoint, credential=account_key)

            # Create a ContainerClient
            container_client = blob_service_client.get_container_client(container_name)


            # # Download the blob from Azure Blob Storage
            # downloaded_blob_name = 'train_v1.zip'
            blob_client = container_client.get_blob_client(downloaded_blob_name)
            with open(downloaded_blob_name, "wb") as data:
                blob_data = blob_client.download_blob()
                data.write(blob_data.readall())

            zip_file = ZipFile(downloaded_blob_name, 'r')
            if os.path.exists(self.data_dir):
                shutil.rmtree(self.data_dir)
                print("Removed Old Data.")
            os.makedirs(self.data_dir)
            zip_file.extractall(self.data_dir)
            self.CLASSES = os.listdir(self.data_dir)
            self.CLASSES_LEN = len(self.CLASSES)
            print("Extracting data in ", self.data_dir)
        else:
            raise ValueError("Cloud service with name "+csp+" not supported.")


    
