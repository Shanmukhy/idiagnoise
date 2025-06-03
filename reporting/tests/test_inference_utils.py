import unittest
from utils.utils import GenAIChatBot, ContentItem
from pydicom import Dataset, Sequence

class TestGenAIChatBot(unittest.TestCase):
    def setUp(self):
        self.conditions = ['Mass', 'Infiltration', 'No_Finding', 'Hernia']
        self.chatbot = GenAIChatBot(self.conditions)

    def test_handle_query_positive(self):
        # Test when user input contains both medical condition and classification keyword
        user_input = "does the patient is suffering from hernia"
        result = self.chatbot.handle_query(user_input)
        self.assertEqual(result, "hernia")

    def test_handle_query_negative(self):
        # Test when user input doesn't contain medical condition and classification keyword
        user_input = "invalid query"
        result = self.chatbot.handle_query(user_input)
        self.assertEqual(result, "Insufficient data")

    def test_get_medical_keywords(self):
        # Test extracting medical keyword from the document
        doc = self.chatbot.nlp("Does the patient shows symptoms of mass")
        result = self.chatbot.get_medical_keywords(doc)
        self.assertEqual(result, "mass")

    def test_query_inference_result_with_dict(self):
        # Test querying inference result with dictionary
        inference = {"mass": 0.8, "hernia": 0.6, "infiltration": 0.4}
        keyword = "mass"
        result = self.chatbot.query_inference_result(keyword,inference)
        expected_result = "The patient shows signs of mass (confidence:0.8)."
        self.assertEqual(result, expected_result)

    def test_query_inference_result(self):
        keyword = "mass"
        inference = {"mass": 0.3, "hernia": 0.6, "infiltration": 0.4}
        result = self.chatbot.query_inference_result(keyword,inference) 
        self.assertEqual(result, "Patient doesn't shows signs of mass.But there is signs of hernia (confidence:0.6).")

    def test_query_inference_result_with_dict_failed(self):
        keyword = "mass"
        inference = {"mass": 0.2,"pneumonia":0.12}
        result = self.chatbot.query_inference_result(keyword,inference) 
        self.assertEqual(result, "There is no signs of mass (confidence:0.2).")

    def test_query_inference_result_with_string(self):
        # Test querying inference result with a string
        inference = "mass"
        keyword = "mass"
        result = self.chatbot.query_inference_result(keyword,inference)
        expected_result = "The patient shows signs of mass."
        self.assertEqual(result, expected_result)

    def test_query_inference_result_with_string(self):
        # Test querying inference result with a string
        inference = "hernia"
        keyword = "mass"
        result = self.chatbot.query_inference_result(keyword,inference)
        expected_result = "The patient does not show signs of mass."
        self.assertEqual(result, expected_result)

    def test_query_inference_result_insufficient_data(self):
        # Test querying inference result with insufficient data
        inference = None
        keyword = "hernia"
        result = self.chatbot.query_inference_result(keyword,inference)
        expected_result = "Not enough data"
        self.assertEqual(result, expected_result)


class TestContentItem(unittest.TestCase):
    def test_init(self):
        # Test initialization without value
        content_item_without_value = ContentItem("CODE", "SCHEME", "Content")
        self.assertEqual(content_item_without_value.code_value, "CODE")
        self.assertEqual(content_item_without_value.coding_scheme_designator, "SCHEME")
        self.assertEqual(content_item_without_value.code_meaning, "Content")

        # Test initialization with value
        content_item_with_value = ContentItem("CODE", "SCHEME", "Value", "NUM", 100)
        self.assertEqual(content_item_with_value.code_value, "CODE")
        self.assertEqual(content_item_with_value.coding_scheme_designator, "SCHEME")
        self.assertEqual(content_item_with_value.code_meaning, "Value")
        self.assertEqual(content_item_with_value.value_type, "NUM")
        self.assertEqual(content_item_with_value.value, 100)

    def test_get_dicom_ds(self):
        # Test getting DICOM dataset without value
        content_item = ContentItem("CODE", "SCHEME", "Content")
        ds = content_item.get_dicom_ds()
        self.assertIsInstance(ds, Dataset)
        self.assertEqual(ds.CodeValue, "CODE")
        self.assertEqual(ds.CodingSchemeDesignator, "SCHEME")
        self.assertEqual(ds.CodeMeaning, "Content")

    def test_get_content_item(self):
        # Test getting content item with numeric value
        content_item_with_numeric_value = ContentItem("CODE", "SCHEME", "Value", "NUM", 100)
        ds = content_item_with_numeric_value.get_content_item()
        self.assertEqual(ds.ValueType, "NUM")
        self.assertEqual(ds.NumericValue, 100)

        content_item_with_text_value = ContentItem("CODE", "SCHEME", "Value", "TEXT", "100")
        ds = content_item_with_text_value.get_content_item()
        self.assertEqual(ds.ValueType, "TEXT")
        self.assertEqual(ds.TextValue, "100")

        content_item_with_dt_value = ContentItem("CODE", "SCHEME", "Value", "DATETIME", "20000101101010")
        ds = content_item_with_dt_value.get_content_item()
        self.assertEqual(ds.ValueType, "DATETIME")
        self.assertEqual(ds.DateTime, "20000101101010")

        content_item_with_date_value = ContentItem("CODE", "SCHEME", "Value", "DATE", "20000101")
        ds = content_item_with_date_value.get_content_item()
        self.assertEqual(ds.ValueType, "DATE")
        self.assertEqual(ds.Date, "20000101")

        content_item_with_time_value = ContentItem("CODE", "SCHEME", "Value", "TIME", "101010")
        ds = content_item_with_time_value.get_content_item()
        self.assertEqual(ds.ValueType, "TIME")
        self.assertEqual(ds.Time, "101010")

        content_item_with_uid_value = ContentItem("CODE", "SCHEME", "Value", "UIDREF", "1.2.3.4")
        ds = content_item_with_uid_value.get_content_item()
        self.assertEqual(ds.ValueType, "UIDREF")
        self.assertEqual(ds.UID, "1.2.3.4")

    

