from utils.utils import DicomService
import pydicom
from unittest.mock import patch, MagicMock

dicom_utils = DicomService()

def test_create_ds_from_request_body():
    request_body={"PatientID":"Anon12345", "Modality":"CT"}
    ds_result= dicom_utils.create_ds_from_request_body(request_body)
    ds =pydicom.Dataset()
    ds.PatientID= "Anon12345"
    ds.Modality = "CT"
    assert ds==ds_result
	

@patch('utils.utils.AE')
def test_c_find_pacs_success(mock_ae):
    # Mock the AE class and its methods
    mock_assoc = MagicMock()
    mock_ae.return_value.associate.return_value = mock_assoc
    mock_ds = MagicMock()

    # Define the expected response from the C-FIND operation
    mock_response = [
        (MockStatus(0xFF00), MockIdentifier(patient_id = "test", study_uid="1.2.3.4", series_uid="1.2.3.4.1")),
        (MockStatus(0xFF00), MockIdentifier(patient_id = "test", study_uid="1.2.3.4", series_uid="1.2.3.4.2")),
        (MockStatus(0xFF00), MockIdentifier(patient_id = "test", study_uid="2.3.4", series_uid="2.3.4.1"))
        ]

    mock_assoc.send_c_find.return_value = mock_response

    # Call the function
    dummy_port = 1234
    result = dicom_utils.c_find_pacs(mock_ds, 'dummy_host', dummy_port)

    # Assert the result
    expected_result = [
    {
        "PatientID": "test",
        "studies": [
        {
            "series": [
            {
                "series_uid": "1.2.3.4.1"
            },
            {
                "series_uid": "1.2.3.4.2"
            }
            ],
            "study_uid": "1.2.3.4"
        },
        {
            "series": [
            {
                "series_uid": "2.3.4.1"
            }
            ],
            "study_uid": "2.3.4"
        }
        ]
    }
    ]
        
    assert result['status'] == 200
    assert result['message'] == expected_result

    #Assert that associate and release methods were called
    mock_ae.return_value.associate.assert_called_once_with('dummy_host', dummy_port)
    mock_assoc.release.assert_called_once()

@patch('utils.utils.AE')
def test_c_find_pacs_association_failure(mock_ae):
    # Mock the AE class to simulate an association failure
    mock_ae.return_value.associate.return_value.is_established = False
    mock_ds = MagicMock()

    # Call the function
    dummy_port = 1234
    result = dicom_utils.c_find_pacs(mock_ds, 'dummy_host', dummy_port)

    # Assert the result
    expected_result = {'status':500, 'message': 'Failed to establish association with PACS server'}
    assert result==expected_result

    # Assert that associate method was called
    mock_ae.return_value.associate.assert_called_once_with('dummy_host', dummy_port)

@patch('utils.utils.AE')
def test_c_find_pacs_nostudy(mock_ae):
    # Mock the AE class and its methods
    mock_assoc = MagicMock()
    mock_ae.return_value.associate.return_value = mock_assoc
    mock_ds = MagicMock()

    # Define the expected response from the C-FIND operation
    mock_response = [
        (MockStatus(0x0000), MockIdentifier(patient_id = "test", study_uid="1.2.3.4", series_uid="1.2.3.4.1")),
        (MockStatus(0x0000), MockIdentifier(patient_id = "test", study_uid="1.2.3.4", series_uid="1.2.3.4.2")),
        (MockStatus(0x0000), MockIdentifier(patient_id = "test", study_uid="2.3.4", series_uid="2.3.4.1"))
        ]

    mock_assoc.send_c_find.return_value = mock_response

    # Call the function
    dummy_port = 1234
    result = dicom_utils.c_find_pacs(mock_ds, 'dummy_host', dummy_port)
    expected_result = {'message': [], 'status': 200}

    assert result == expected_result

    #Assert that associate and release methods were called
    mock_ae.return_value.associate.assert_called_once_with('dummy_host', dummy_port)
    mock_assoc.release.assert_called_once()

# Mock classes for DICOM Status and Identifier
class MockStatus:
    def __init__(self, status):
        self.Status = status

class MockIdentifier:
    def __init__(self, patient_id, study_uid, series_uid):
        self.PatientID = patient_id
        self.StudyInstanceUID = study_uid
        self.SeriesInstanceUID = series_uid