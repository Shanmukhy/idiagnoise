import json

class Config:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config_data = self.load_config()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as file:
                config_data = json.load(file)
                #print(f"Loaded configuration: {config_data}")
                return config_data
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found at path: {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in config file: {self.config_path}")

    def read_config(self, config_key):
        return self.config_data.get(config_key, {})
    
    def read_model_config(self, path):
        data = json.load(open(path, 'r'))
        return data
    
    def set_model_config(self, data, args):
        model_params = data[args.model]
        args.img_height = model_params['img_height']
        args.img_width = model_params['img_width']
        args.batch_size = model_params['batch_size']
        args.epochs = model_params['epochs']
        args.learning_rate = model_params['learning_rate']
        
        return args
