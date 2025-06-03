from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelFind, PatientRootQueryRetrieveInformationModelGet, CTImageStorage
from pynetdicom import AE, build_role, evt
import pydicom
from io import BytesIO
import os

class DicomService():
    def __init__(self):
        self.output_list = []
        self.handlers = [(evt.EVT_C_STORE, self.handle_store)]

    def create_folder_and_write_file(self, parent, folder_name, file_name, content):
        folder_path = os.path.join(parent, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'wb') as file:
            file.write(content)

    def create_ds_from_request_body(self, request):
        """
        Creates Pydicom dataset from request body. This shall be used to send C-FIND and C-GET requests to PACS server
        Args:
            request(dict): Request body from client containing DICOM Tag and corresponding value to search and retrieve data
        Returns:
            pydicom.Dataset: pydicom.Dataset object that contains the query terms.
        """
        ds = pydicom.Dataset()
        for key, value in request.items():
            setattr(ds, key, value)
        return ds
    
    def c_find_pacs(self, ds, hostname, port):
        """
        Sends C-FIND request to PACS Server to look for DICOM data matching the query parameters
        Args:
            ds(pydicom.Dataset): pydicom.Dataset object that contains the query terms. Created using create_ds_from_request_body method of this class.
            hostname(str): Hostname/IP of the PACS server
            port(int): Port Number to connect to PACS server
        Returns:
            dict: Response of the query operation
                A nested JSON with Series and Study UIDs available for each PatientID that matches the query.
        """
        # Create Association
        ae = AE(ae_title="iDiagnose")
        ae.add_requested_context('1.2.840.10008.1.1')
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)
        assoc = ae.associate(hostname, port)
        ds.QueryRetrieveLevel = "SERIES"
        if not "StudyInstanceUID" in ds:
            ds.StudyInstanceUID = []
        if not "SeriesInstanceUID" in ds:
            ds.SeriesInstanceUID = []
        if not "PatientID" in ds:
            ds.PatientID  =[]
        result = {}
    
        # Get C_FIND response
        if assoc.is_established:
            responses = assoc.send_c_find(ds, PatientRootQueryRetrieveInformationModelFind)
            for (status, identifier) in responses:
                if status.Status == 0xFF00:
                    patient_id = identifier.PatientID
                    study_id = identifier.StudyInstanceUID
                    series_id = identifier.SeriesInstanceUID

                    if patient_id not in result:
                        result[patient_id] = {"PatientID": patient_id, "studies": []}

                    current_patient = result[patient_id]["studies"]

                    if not any(study["study_uid"] == study_id for study in current_patient):
                        current_patient.append({"study_uid": study_id, "series": []})

                    current_study = next(study for study in current_patient if study["study_uid"] == study_id)

                    if series_id not in [series["series_uid"] for series in current_study["series"]]:
                        current_study["series"].append({"series_uid": series_id})

            
            formatted_result = [{"PatientID": patient["PatientID"], "studies": patient["studies"]} for patient in result.values()]
            assoc.release()
            return {'status':200 ,"message":formatted_result}  # Return the response dictionary
        else:
            return {'status':500, 'message': 'Failed to establish association with PACS server'}
        
    def c_get_pacs(self, ds, hostname, port):
        """
        Sends C-GET request to PACS Server to retrieve DICOM data matching the query parameters
        Args:
            ds(Pydicom.Dataset): pydicom.Dataset object that contains the query terms. Created using create_ds_from_request_body method of this class.
            hostname(str): Hostname/IP of the PACS server
            port(int): Port Number to connect to PACS server
        Returns:
            dict: Response of the retrieve operation
                Returns DICOM byte data inside a list if success(200 status), else error message.
        """
        ae = AE(ae_title=b'iDiagnose')
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)
        ae.add_requested_context('1.2.840.10008.1.1')
        assoc = ae.associate(hostname, port)
        get_ds = ds.copy()
        ds.QueryRetrieveLevel = "SERIES"
        ds.SOPClassUID = []

        # Get C_FIND response
        sop_classes = []
        if assoc.is_established:
            print("Here")
            responses = assoc.send_c_find(ds, PatientRootQueryRetrieveInformationModelFind)
            for (status, identifier) in responses:
                if status.Status == 0xFF00:
                    sop_classes.append(identifier.SOPClassUID)
            assoc.release()
        else:
            return {'status': 500, 'message': 'Failed to establish association with PACS'}
        ae = AE(ae_title="iDiagnose")
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelGet)
        roles = []
        for sop_class in sop_classes:
            ae.add_requested_context(sop_class)
            roles.append(build_role(sop_class, scp_role=True))
        assoc = ae.associate(hostname, port, ext_neg=roles, evt_handlers=self.handlers)

        if assoc.is_established:
            get_ds.QueryRetrieveLevel = "SERIES"

            responses = assoc.send_c_get(get_ds, PatientRootQueryRetrieveInformationModelGet)
            for status, identifier in responses:
                print(identifier)
                if status.Status == 0xFF00:
                    print('C-GET query status: 0x{0:04x}'.format(status.Status))
                elif status.Status == 0x0000:
                    print('C-GET Completed')
                else:
                    return {'status': 404, 'message': 'Requested data is not available in the PACS'}

            assoc.release()
            return {'status': 200, 'message': 'Data retrieved', 'retrieved_data': self.output_list}
        else:
            return {'status': 500, 'message': 'Failed to establish association with PACS'}
         
    def handle_store(self, event):
        """
        Event to handle storage of DICOM data from C-GET request.
        """
        dicom_bytes_io = BytesIO()
        ds = event.dataset
        ds.file_meta = event.file_meta
        ds.save_as(dicom_bytes_io, write_like_original=False)
        dicom_bytes_io.seek(0)

        self.output_list.append(dicom_bytes_io)
        return 0x0000
    
    def separate_series(self, series):
        result = []
        for patient_data in series:
            # print(patient_data)
            patient_id = patient_data['PatientID']
            studies = patient_data['studies']
            
            for study in studies:
                study_uid = study['study_uid']
                series_list = study['series']
                
                for series_data in series_list:
                    series_uid = series_data['series_uid']
                    
                    patient_info = {
                        'PatientID': patient_id,
                        'StudyInstanceUID': study_uid,
                        'SeriesInstanceUID': series_uid
                    }
                    result.append(patient_info)
        
        return result