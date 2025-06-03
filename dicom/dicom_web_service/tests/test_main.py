from unittest.mock import patch, mock_open
from main import app, dcmweb_ping_server
import pytest
import os

config_path = os.path.join("config", "config.json")

@pytest.fixture
def mock_file_open():
    # Create a mock for the built-in open function
    m = mock_open()
    with patch('builtins.open', m, create=True):
        yield m

@patch('main.dcmweb_ping_server')
def test_config_ping_success(mock_ping, mock_file_open):
    mock_ping.return_value = {'message': 'DICOMWeb Server Connection Verified'}, 200
    with app.test_client() as client:
        response = client.post('/api/configure', json={'url': 'dummyhost', 'root': "dummy", 'auth': ['test', 'test']})
    mock_file_open.assert_called_once_with(config_path, 'w')
    assert response.status_code == 200
    assert response.get_json()['message'] == 'PACS location added successfully'
    assert response.get_json()['c-echo'] == "verified"

@patch('main.dcmweb_ping_server')
def test_config_ping_failure(mock_ping, mock_file_open):
    mock_ping.return_value = {'message': 'Unable to establish connection with DICOMWeb Server'}, 405
    with app.test_client() as client:
        response = client.post('/api/configure', json={'url': 'dummyhost', 'root': "dummy", 'auth': ['test', 'test']})
    mock_file_open.assert_called_once_with(config_path, 'w')
    assert response.status_code == 201
    assert response.get_json()['message'] == 'PACS location added successfully'
    assert response.get_json()['c-echo'] == "failed"

def test_config_missparams(mock_file_open):
    with app.test_client() as client:
        response = client.post('/api/configure', json={'url': 'dummyhost', 'auth': ['test', 'test']})
    mock_file_open.assert_called_once_with(config_path, 'w')
    assert response.status_code == 400
    assert response.get_json()['message'] == 'Not enough configuration parameters'

@patch("main.requests.get")
def test_ping_dicomweb_server_success(mock_get):
    mock_get.return_value.status_code = 200
    with app.test_client() as client:
        response = client.get('/api/ping')
    assert response.json["message"] == 'DICOMWeb Server Connection Verified'
    assert response.status_code == 200

@patch("main.requests.get")
def test_ping_dicomweb_server_unauthorized(mock_get):
    mock_get.return_value.status_code = 401  
    with app.test_client() as client:
        response = client.get('/api/ping')
    assert response.json['message'] == 'Unable to establish connection with DICOMWeb Server'
    assert response.status_code == 405

@patch("main.requests.get")
def test_ping_dicomweb_server_exception(mock_get):
    mock_get.side_effect = Exception("TestException")
    with app.test_client() as client:
        response = client.get('/api/ping')
    assert response.json['message'] == 'DICOMWeb Server not available'
    assert response.status_code == 404