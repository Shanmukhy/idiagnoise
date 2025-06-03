import pytest
from main import ReportGeneration
import numpy as np
import fitz
from PIL import Image
import os
import pydicom

@pytest.fixture
def report_generator():
    return ReportGeneration()

def test_extract_dicom_info(report_generator):
        with open(r"tests/test_data/I10", "rb") as file:
            actual_dicom_data = file.read()
        actual_result = report_generator.extract_dicom_info(actual_dicom_data)
        expected_result = {
            "PatientID": actual_result['PatientID'], 
            "PatientName": actual_result['PatientName'],
            "PatientAge": actual_result['PatientAge'],
            "PatientGender": actual_result['PatientGender'],
            "ReferringPhysician": actual_result['ReferringPhysician'],
            "StudyDateTime": actual_result['StudyDateTime'],
            "SeriesInstanceUID": actual_result['SeriesInstanceUID']
        }
        assert actual_result == expected_result

def test_dcm_to_numpy(report_generator):    
    dcm_file_path = "tests/test_data/I10"
    dcm_data = pydicom.dcmread(dcm_file_path)
    actual_pixel_array = dcm_data.pixel_array

    # Convert DICOM data to numpy array using the function under test
    with open(dcm_file_path, "rb") as file:
        dicom_data = file.read()
    pixel_array = report_generator.dcm_to_numpy(dicom_data)

    # Compare the dimensions and content of the actual and converted pixel arrays
    assert isinstance(pixel_array, np.ndarray)
    assert pixel_array.shape == actual_pixel_array.shape
    assert np.array_equal(pixel_array, actual_pixel_array)

def test_overlay_text(report_generator):    
    with open(r"tests/test_data/I10", "rb") as file:
        dicom_data = file.read() 
    inference_result = "Sample inference result" 
    actual_result = report_generator.overlay_text(dicom_data, inference_result) 
    expected_result = Image.open("tests/test_data/test-expected.png")    
    actual_result = np.array(actual_result)
    expected_result = np.array(expected_result)
    assert np.array_equal(actual_result, expected_result)
    
def test_generate_report(report_generator):    
    with open("tests/test_data/I10", "rb") as file:
        dicom_data = file.read()
    inference_result = "Test inference result"
    # Generate the report
    output_file = report_generator.generate_report(inference_result, dicom_data)
    # Check if the output file exists
    assert os.path.exists(output_file)
    # Check if the generated PDF is not empty
    assert os.path.getsize(output_file) > 0
    # extract text content from the generated PDF
    doc = fitz.open(output_file)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    doc.close()
    # Expected text content from a reference PDF
    with open("tests/test_data/Intermediate_Report.pdf", "rb") as expected_file:
        expected_text = expected_file.read()
    # Check if the actual text matches the expected text
    assert text.strip() == expected_text.strip()
        