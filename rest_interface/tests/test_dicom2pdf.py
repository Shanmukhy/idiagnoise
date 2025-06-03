import pytest
import numpy as np
import os
from utils.image_utils.dicom2pdf import PdfGeneration

@pytest.fixture
def pdf_instance():
    return PdfGeneration()

@pytest.fixture
def dicom_byte_data():
    with open(r"tests/datas/I10", 'rb') as file:
        return file.read()

def test_dicom_to_numpy(pdf_instance, dicom_byte_data):
    actual_result = pdf_instance.dicom_to_numpy(dicom_byte_data)
    assert actual_result is not None
    expected_result = np.load("tests\datas\pixel_array.npy")
    assert np.array_equal(actual_result, expected_result)

def test_dicom_to_numpy_invalid_byte_data(pdf_instance):
    with pytest.raises(ValueError):
        pdf_instance.dicom_to_numpy(None)

def test_byte_to_pdf(pdf_instance, dicom_byte_data):
    result = pdf_instance.byte_to_pdf(dicom_byte_data)
    expected_result = r"tests/datas/output.pdf"
    assert os.path.exists(expected_result)
    with open(expected_result, "rb") as file:
        expected_content = file.read()
    assert result == expected_content
           
def test_byte_to_pdf_invalid_byte_data(pdf_instance):
    with pytest.raises(ValueError):
        pdf_instance.byte_to_pdf(None)

def test_byte_to_pdf_content(pdf_instance, dicom_byte_data):
    result = pdf_instance.byte_to_pdf(dicom_byte_data)
    assert b'%PDF' in result   #check pdf header contains 
