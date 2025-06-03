from utils.utils import DicomwebService
import json
from unittest.mock import patch, MagicMock

service = DicomwebService()

def test_dicom_web_query_not_valid_tag():
    response=service.dicom_web_query("test",{"Patient_id":"001"},auth=["test","test"])
    expected_response={"Message":"Not a valid tag","status":400}
    assert response == expected_response

def test_dicom_web_query_empty_request_body():
    response=service.dicom_web_query("test",{},auth=["test","test"])
    expected_response={ "Message":"Request body is empty","status":400}
    assert response == expected_response

@patch("utils.utils.requests.get")
def test_dicom_web_query(mock_get):
    mock_response = MagicMock()
    with open("tests/mockresponse-dcmwebquery.json", "r") as json_file:
        mock_response.json.return_value = json.load(json_file)["mock_response"]
        mock_get.return_value = mock_response

    response = service.dicom_web_query("test", {"PatientID":"Anon*"}, auth = ["test","test"])
    expected_response= [{'PatientID': 'Anon12345', 'studies': [{'study_uid': '1.2.840.113619.2.359.3.17471110.114.1545111224.486', 'series': [{'series_uid': '1.2.826.0.1.3680043.8.498.19777489053532190969315062455803832947'}]}, {'study_uid': '1.2.840.113619.2.359.3.17471110.114.1545111230.486', 'series': [{'series_uid': '1.2.826.0.1.3680043.8.498.83203011545148119733000464118249565196'}]}]}, {'PatientID': 'Anon027', 'studies': [{'study_uid': '1.2.840.113619.2.359.3.17471110.73.1544246088.52', 'series': [{'series_uid': '1.2.826.0.1.3680043.8.498.22841129883617681617913305465008737526'}]}]}, {'PatientID': 'Anon80', 'studies': [{'study_uid': '1.2.840.113619.2.359.3.17471110.908.1544864487.814', 'series': [{'series_uid': '1.2.826.0.1.3680043.8.498.48596288019045877193410010995695759250'}]}]}]

    assert response['message'] == expected_response
    assert response['status'] == 200