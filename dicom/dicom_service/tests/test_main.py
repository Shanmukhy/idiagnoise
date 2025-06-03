from main import app, echo_pacs, query_pacs
from unittest.mock import patch, MagicMock, mock_open
import pytest
from flask import jsonify
import os

config_path = os.path.join("config", "config.json")
@pytest.fixture
def mock_file_open():
    # Create a mock for the built-in open function
    m = mock_open()
    with patch('builtins.open', m, create=True):
        yield m

@patch('main.echo_pacs')
def test_config_echo_success(mock_echo_pacs, mock_file_open):
    mock_echo_pacs.return_value = {'message': 'C-ECHO failure'}, 200
    with app.test_client() as client:
        response = client.post('/api/configure', json={'address': 'dummyhost', 'port': 0, 'ae_title': 'TESTAE'})

    mock_file_open.assert_called_once_with(config_path, 'w')
    assert response.status_code == 200
    assert response.get_json()['message'] == 'PACS location added successfully'
    assert response.get_json()['c-echo'] == "verified"

@patch('main.echo_pacs')
def test_config_echo_failure(mock_echo_pacs, mock_file_open):
    mock_echo_pacs.return_value = {'message': 'C-ECHO failure'}, 400
    with app.test_client() as client:
        response = client.post('/api/configure', json = {"address": "dummyhost", "port" : 0, "ae_title": "TESTAE"})
    mock_file_open.assert_called_once_with(config_path, 'w')
    assert response.status_code == 201
    assert response.get_json()['message'] =='PACS location added successfully'
    assert response.get_json()['c-echo'] == 'failed'

def test_config_missparams(mock_file_open):
    with app.test_client() as client:
        response = client.post('/api/configure', json = {"address": "dummyhost", "ae_title": "TESTAE"})
    mock_file_open.assert_called_once_with(config_path, 'w')
    assert response.status_code == 400
    assert 'Not enough configuration parameters' in response.get_json()['message']

@patch('main.AE')
def test_echo_pacs_success(mock_ae):
    # Mock the AE class and its methods
    mock_assoc = MagicMock()
    mock_ae.return_value.associate.return_value = mock_assoc
    mock_response = MockStatus(0x0000)
    mock_assoc.send_c_echo.return_value = mock_response

    with app.test_client() as client:
        response = client.get('/api/echo')

    assert response.json == {'message': 'C-ECHO successful'}
    assert response.status_code == 200

@patch('main.AE')
def test_echo_pacs_failure(mock_ae):
    # Mock the AE class and its methods
    mock_assoc = MagicMock()
    mock_ae.return_value.associate.return_value = mock_assoc
    mock_response = MockStatus(0xFFFF)
    mock_assoc.send_c_echo.return_value = mock_response

    with app.test_client() as client:
        response = client.get('/api/echo')
    
    assert response.json == {'message': 'C-ECHO failure'}
    assert response.status_code == 400 

@patch('main.AE')
def test_echo_association_failure(mock_ae):
    # Mock the AE class and its methods
    mock_assoc = MagicMock()
    mock_assoc.is_established = False
    mock_ae.return_value.associate.return_value = mock_assoc

    with app.test_client() as client:
        response = client.get('/api/echo')
    
    assert response.json == {'message': 'Failed to establish association with PACS server'}
    assert response.status_code == 404
    
class MockStatus:
    def __init__(self, status):
        self.Status = status