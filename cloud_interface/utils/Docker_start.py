import docker

class Docker:
    def __init__(self):
        pass
    def is_image_present(self,image_name):
        try:
            client = docker.from_env()
            print(f"Debug: Created Docker client")
            client.images.get(image_name)
            print(f"Debug: Retrieved image {image_name}")
            return True
        except docker.errors.ImageNotFound:
            print(f"Debug: Image {image_name} not found")
            return False

    def start_container_by_id(self,train_id, image_name, request_params):
        try:
            client = docker.from_env()
            expected_args = ["img_height", "img_width", "batch_size", "epochs", "model", "transfer_learning_model_id", "learning_rate"]
            input_args = []
            for arg in expected_args:
                if arg in request_params:
                    input_args.extend(['--' + arg, str(request_params[arg])])
            
            print(input_args)

            container = client.containers.run(image_name, name=train_id, network_mode = "host", 
                                              device_requests=[docker.types.DeviceRequest(device_ids=["all"], capabilities=[['gpu']])],
                                              command=input_args)

            print(f"Container started successfully with image '{image_name}'.")
        except docker.errors.NotFound:
            print(f"Container not found.")
        except docker.errors.APIError as e:
            print(str(e))
            print(f"Error starting container with ID")