import pytest
from flask.testing import FlaskClient
from main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_generate_report(client: FlaskClient):
    dicom_data_path = "tests/test_data/I10"
    inference_results = {"AI findings": "Findings"}

    with open(dicom_data_path, 'rb') as file:
        dicom_data = file.read()

    data = {
        'dicom_data': (dicom_data, 'test.dcm'),
        'inference_results': inference_results
    }
    response = client.post('/create-interim-report', data=data, content_type='multipart/form-data')
    print(response.json)
    json_data = response.json
    assert 'file' in json_data
    assert 'PatientID' in json_data
    assert 'SeriesUID' in json_data

def test_generate_report_error(client):
    data = {
        'inference_results': 'Your inference results'
    }
    response = client.post('/create-interim-report', data=data)    
    assert response.status_code == 500
    json_data = response.json
    assert 'Error' in json_data
