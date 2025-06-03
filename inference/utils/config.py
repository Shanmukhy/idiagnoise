import json

class Config:
    def __init__(self, file_path,config_path):
        self.file_path = file_path
        self.config_path = config_path

    def get_version_id(self):
        try:
            data = json.load(open(self.file_path, 'r'))
        except Exception as e:
            raise FileNotFoundError
        return data['version_id']
    
    def get_server_conf(self):
        try:
            data = json.load(open(self.config_path, 'r'))
        except Exception as e:
            raise FileNotFoundError
        return data
    
    def get_server_port_ip(self, server_name):
        try:
            conf = self.get_server_conf()
            data = conf[server_name]
            ip = data['ip']
            port = data['port']
        except Exception as e:
            raise ValueError
 
        return ip, port