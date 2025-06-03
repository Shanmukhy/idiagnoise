import argparse

import os
import shutil
import json

from model.rapid_model import RapidModel
from model.custom_model import Model
from model.model_utils import ModelMeta
from utils.dataprocessing import Dataset
from utils.collection import ModelCollection
from utils.config import Config

# Function to parse command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Train model on Lungs Xray dataset.")
    parser.add_argument("--img_height", type=int, default=224, help="Height of the input images")
    parser.add_argument("--img_width", type=int, default=224, help="Width of the input images")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size for training")
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs for training")
    parser.add_argument("--model", type=str, default="custom", required=True, help="Provide the model name, from list: [resnet50, mobilenet, mobilenetv2, vgg16, vgg19, xception, custom]")
    parser.add_argument("--transfer_learning_model_id", type=str, default=None, help="Perform Transfer Learning with provided model version.")
    parser.add_argument("--learning_rate", type=float, default=0.001, help="Provide model learning rate.")
    parser.add_argument("--csp", type=str, default="azure", help="provide the name for cloud service provider. Select Azure/AWS.")
    parser.add_argument("--train_data_id", type=str, default=None, help="Load the training dataset as per training id.")

    return parser.parse_args()



if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_args()
    cfg = Config("config/config.json")

    model_meta = ModelMeta()

    mongo_server = cfg.read_config(config_key="mongo_server")
    model_collection = ModelCollection(mongo_server)

    training_blob_cred = cfg.read_config(config_key="training_data_blob")

    SAVED_MODEL_DIR = "./model/"

    dataset = Dataset('./data', args.img_height, args.img_width, mongo_server)
    dataset.download_from_cloud(training_blob_cred, args.csp, args.train_data_id)

    train_ds = dataset.get_train_data(args.batch_size)
    val_ds = dataset.get_val_data(args.batch_size)

    if args.model == "custom":
        rpd_model = Model(dataset.CLASSES_LEN)    
    else:
        rpd_model = RapidModel(dataset.CLASSES_LEN)

    # If model is RapidModel and Training from scratch.
    if args.transfer_learning_model_id == None and args.model != "custom":
        rpd_model.load_fortraining(args.model, args.img_height, args.img_width, args.learning_rate)

    # If model is Custom model and Training from Scratch.
    elif args.transfer_learning_model_id == None and args.model == "custom":
        rpd_model.load_fortraining(args.model, args.img_height, args.img_width, args.learning_rate)

    # If model is RapidModel/Custom and Transfer learning is enabled.
    else: #args.transfer_learning_model_id != None and args.model != "custom":
        model_collection.download_model(SAVED_MODEL_DIR, args.model, args.transfer_learning_model_id)
        rpd_model.load_frompretrained(SAVED_MODEL_DIR, args.learning_rate)

    print("Training the Model.")
    rpd_model.train(train_ds, val_ds, args.epochs)
    
    rpd_model.get_val_test_accuracy()
    
    if rpd_model.is_model_validated(accuracy=0.001):
            
        # # If model is Custom model and transfer learning is enabled.
        # elif args.transfer_learning_model_id != None and args.model == "custom":
        #     model_collection.download_model(SAVED_MODEL_DIR, args.model, args.transfer_learning_model_id)
        #     rpd_model.load_frompretrained(SAVED_MODEL_DIR)
        #     rpd_model.train(train_ds, val_ds, args.epochs)
            

        model_path = SAVED_MODEL_DIR+'/'+args.model+"_lungs"
        rpd_model.save(model_path)

        print("Saved TF model.")
        name = model_meta.generate_model_name()
        vid = model_meta.generate_version_id()
        archived = shutil.make_archive(name, 'zip', model_path)
        
        if os.path.exists(archived):
            print("Model Zip File Created: ", archived) 
            model_collection.upload_model(archived, args.model, vid)
        else: 
            print("Something went Wrong! Model Zip file not created.")
