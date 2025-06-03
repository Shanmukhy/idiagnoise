from datetime import datetime

class ModelMeta:
    def __init__(self):
        pass
    def generate_model_name(self):
        # Get the current date and time
        current_date = datetime.now().strftime("%d%m%Y_%H%M%S")#("%Y%m%d_%H%M%S")

        # Create a unique model ID with the initial 'm' and date/time details
        model_id = f"model_{current_date}"

        # Concatenate the model ID and format to create the final model name
        model_name = f"{model_id}"
 
        return model_name

    def generate_current_datetime(self):
        # Get the current date and time
        current_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        return current_datetime

    def generate_version_id(self):
        # Get the current date and time
        current_datetime = datetime.now().strftime("%H%M%S%Y%m%d")

        # Create a unique model ID with the initial 'm' and date/time details
        version_name = f"V{current_datetime}"

        # Concatenate the model ID and format to create the final model name
        version_id = f"{version_name}"


        return version_id