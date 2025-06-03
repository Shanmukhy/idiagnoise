import io
import os
import numpy as np
import pydicom
from pydicom.pixel_data_handlers.util import apply_windowing
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

class PdfGeneration():
    def __init__(self):
        pass

    def dicom_to_numpy(self, byte_data):
        """
        Converts DICOM data to a NumPy array.

        Args:
        - byte_data (bytes): Byte data of the DICOM file.
        
        Returns:
        - NumPy array: Pixel data of the DICOM file.
    
        Raises:
        - ValueError: byte_data is none.
        """
        if byte_data is not None:
            ds = pydicom.dcmread(io.BytesIO(byte_data), force=True)
            return apply_windowing(ds.pixel_array, ds)
        else:
            raise ValueError("No file data or filename provided.")

    def byte_to_pdf(self, byte_data):
        """
        Generates a PDF document from DICOM byte data or a file.

        Args:
        - byte_data (bytes): Byte data of the DICOM file.
        
        Returns:
        - bytes : PDF content as bytes.

        Raises:
        - ValueError: If byte_data is none.
        """
        if byte_data is not None:
            pixel_array = self.dicom_to_numpy(byte_data)
        else:
            raise ValueError("No file data or filename provided.")
        # Normalize pixel values for proper image display
        pixel_array = ((pixel_array - pixel_array.min()) / 
                        (pixel_array.max() - pixel_array.min()) * 255.0).astype(np.uint8)
        image = Image.fromarray(pixel_array)  # numpy array to image
        # Create PDF
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)                
        image.save("temp.png")  # save image temporarily
        c.drawImage("temp.png", 50, 50, width=500, height=600)
        c.showPage()

        # Adding tag information 
        ds = pydicom.dcmread(io.BytesIO(byte_data))
        tag_data = [['Tag', 'Tag Description', 'Value']]
        for elem in ds.file_meta:
            tag_info = [f"({elem.tag.group:04x}, {elem.tag.element:04x})", elem.description(), str(elem.value)]
            tag_data.append(tag_info)
        for elem in ds:
            tag_info = [f"({elem.tag.group:04x}, {elem.tag.element:04x})", elem.description(), str(elem.value)]
            tag_data.append(tag_info)            
            
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        w, h = letter
        max_rows_per_page = 30  
        start_row = 1
        while start_row < len(tag_data):
            end_row = min(start_row + max_rows_per_page, len(tag_data))
            data_for_page = tag_data[start_row:end_row]            
            table = Table(data_for_page)
            table.setStyle(table_style)
            table.wrapOn(c, w, h)
            table.drawOn(c, 10, 10)
            c.setFont("Helvetica", 10)
            c.showPage()
            start_row = end_row
        c.save()
        os.remove("temp.png")     # Clean temporary file
        return pdf_buffer.getvalue()  # Return PDF as bytes
