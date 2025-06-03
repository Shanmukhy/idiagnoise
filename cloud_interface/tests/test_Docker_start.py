import unittest
from unittest.mock import call
from unittest.mock import MagicMock, patch
from docker.errors import ImageNotFound, NotFound, APIError
from utils.Docker_start import Docker

class TestDocker(unittest.TestCase):

    @patch('docker.from_env')
    @patch('docker.models.images.ImageCollection.get')
    def test_is_image_present_true(self, mock_get, mock_docker_from_env):
        # Arrange
        docker_instance = Docker()
        image_name = 'model_training'

        # Act
        result = docker_instance.is_image_present(image_name)

        # Assert
        mock_docker_from_env.assert_called_once()

        # Debug prints
        print(f"Debug: Calls to mock_get: {mock_get.call_args_list}")
        print(f"Debug: Test result: {result}")

        self.assertTrue(result)
   
    
    @patch('docker.from_env')
    @patch('docker.models.containers.ContainerCollection.run')
    def test_start_container_by_id_success(self, mock_run, mock_docker_from_env):
        # Arrange
        docker_instance = Docker()
        train_id = '123'
        image_name = 'model_training'

        # Act
        result = docker_instance.start_container_by_id(train_id, image_name)

        # Assert
        mock_docker_from_env.assert_called_once()
    

if __name__ == '__main__':
    unittest.main()
