from flask import jsonify, Flask
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import json

app = Flask(__name__)
jwt = JWTManager(app)

class UserManagement:
    def __init__(self):
        self.mongo_uri = "mongodb://localhost:27017/"
        self.database_name = "local"   
        self.mongo_client = MongoClient(self.mongo_uri)
        self.mongo_db = self.mongo_client[self.database_name]
        self.collection_name_user="reg_user"
        self.users_collection = self.mongo_db[self.collection_name_user]
  
    def register_user(self, username, password):
        hashed_password = generate_password_hash(password)
        if self.users_collection.find_one({'username': username}):
            return jsonify({'message': f"Username '{username}' already exists"}), 400
        self.users_collection.insert_one({'username': username, 'password': hashed_password})
        return jsonify({'message': f"User '{username}' registered successfully"}), 200

    def login_user(self, username, password):
        user = self.users_collection.find_one({'username': username})
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'message': "Invalid username or password"}), 401
        access_token = create_access_token(identity=username)
        return jsonify({'access_token': access_token}), 200