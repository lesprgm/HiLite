from django.test import TestCase, Client, RequestFactory
from django.contrib.messages import get_messages
from django.http import HttpResponse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, Mock, MagicMock
from io import BytesIO
import json

from .forms import PDFUploadForm
from .utils import clean_text, extract_highlights, extract_highlights_or_fallback
from .views import upload_pdf, connect_to_notion, oauth_callback, send_to_notion, privacy_view, terms_view


class UtilsTestCase(TestCase):
    """Test cases for utility functions in core.utils module"""
    
    def test_clean_text_basic(self):
        """Test basic text cleaning functionality"""
        input_text = "Hello\nWorld!   Multiple   spaces."
        expected = "Hello World! Multiple spaces."
        result = clean_text(input_text)
        self.assertEqual(result, expected)
    
    def test_clean_text_special_characters(self):
        """Test text cleaning removes unwanted special characters"""
        input_text = "Text with $pecial ch@racters & émojis 🚀"
        expected = "Text with pecial chracters mojis "
        result = clean_text(input_text)
        self.assertEqual(result, expected)
    
    def test_clean_text_preserves_punctuation(self):
        """Test that allowed punctuation is preserved"""
        input_text = "Hello, world! How are you? [Good] (Very good): Yes; No."
        expected = "Hello, world! How are you? [Good] (Very good): Yes; No."
        result = clean_text(input_text)
        self.assertEqual(result, expected)
    
    def test_clean_text_empty_string(self):
        """Test clean_text with empty string"""
        result = clean_text("")
        self.assertEqual(result, "")
    
    def test_clean_text_only_newlines_and_spaces(self):
        """Test clean_text with only newlines and spaces"""
        input_text = "\n\n   \n  \n"
        expected = ""
        result = clean_text(input_text)
        self.assertEqual(result, expected)
    
    @patch('core.utils.fitz')
    def test_extract_highlights_with_annotations(self, mock_fitz):
        """Test extract_highlights when PDF has highlight annotations"""
        # Mock PDF document with highlight annotations
        mock_doc = Mock()
        mock_page = Mock()
        mock_annot = Mock()
        
        # Configure mocks
        mock_fitz.open.return_value = mock_doc
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_page.first_annot = mock_annot
        mock_annot.type = [8]  # Highlight annotation type
        mock_annot.vertices = [0, 0, 100, 10, 100, 20, 0, 20, 0, 0, 100, 10, 100, 20, 0, 20]
        mock_annot.next = None
        
        # Mock words and rectangle intersection
        mock_words = [
            [0, 0, 50, 10, "Sample", 0, 0, 0, 0],
            [50, 0, 100, 10, "highlighted", 0, 0, 0, 0],
            [0, 10, 50, 20, "text", 0, 0, 0, 0]
        ]
        
        def mock_get_text(format_type=None):
            if format_type == "words":
                return mock_words
            else:
                return "Sample page text"
        
        mock_page.get_text = Mock(side_effect=mock_get_text)
        
        # Mock fitz.Quad and Rect
        mock_quad = Mock()
        mock_rect = Mock()
        mock_quad.rect = mock_rect
        mock_fitz.Quad.return_value = mock_quad
        mock_fitz.Rect.return_value.intersects.return_value = True
        
        # Create a BytesIO object to simulate file
        pdf_file = BytesIO(b"fake pdf content")
        
        result = extract_highlights(pdf_file)
        
        # Verify the function was called and returned expected results
        mock_fitz.open.assert_called_once()
        self.assertIsInstance(result, list)
    
    @patch('core.utils.fitz')
    def test_extract_highlights_no_annotations(self, mock_fitz):
        """Test extract_highlights when PDF has no annotations"""
        # Mock PDF document without annotations
        mock_doc = Mock()
        mock_page = Mock()
        
        mock_fitz.open.return_value = mock_doc
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_page.get_text.return_value = "Sample page text"
        mock_page.first_annot = None
        
        pdf_file = BytesIO(b"fake pdf content")
        result = extract_highlights(pdf_file)
        
        mock_fitz.open.assert_called_once()
        self.assertEqual(result, [])
    
    @patch('core.utils.vision')
    @patch('core.utils.convert_from_bytes')
    @patch('core.utils.cv2')
    @patch('core.utils.extract_highlights')
    def test_extract_highlights_or_fallback_with_highlights(self, mock_extract, mock_cv2, mock_convert, mock_vision):
        """Test extract_highlights_or_fallback when highlights are found"""
        mock_extract.return_value = ["Found highlight"]
        
        pdf_file = Mock()
        pdf_file.read.return_value = b"fake pdf content"
        
        result = extract_highlights_or_fallback(pdf_file)
        
        self.assertEqual(result, ["Found highlight"])
        mock_extract.assert_called_once()
        # OCR should not be called if highlights are found
        mock_vision.ImageAnnotatorClient.assert_not_called()
    
    @patch('core.utils.vision')
    @patch('core.utils.convert_from_bytes')
    @patch('core.utils.cv2')
    @patch('core.utils.extract_highlights')
    @patch('core.utils.np')
    def test_extract_highlights_or_fallback_ocr_mode(self, mock_np, mock_extract, mock_cv2, mock_convert, mock_vision):
        """Test extract_highlights_or_fallback when no highlights found, falls back to OCR"""
        # Mock no highlights found
        mock_extract.return_value = []
        
        # Mock OCR components
        mock_client = Mock()
        mock_vision.ImageAnnotatorClient.return_value = mock_client
        
        # Mock image processing
        mock_page = Mock()
        mock_convert.return_value = [mock_page]
        
        # Create a mock numpy array that behaves like an image array
        mock_image = Mock()
        mock_image.shape = [100, 200, 3]  # height, width, channels
        mock_image.__getitem__ = Mock(return_value="roi_slice")
        mock_np.array.return_value = mock_image
        
        # Mock OpenCV operations
        mock_cv2.cvtColor.return_value = "hsv_image"
        mock_cv2.inRange.return_value = "mask"
        mock_cv2.dilate.return_value = "dilated_mask"
        mock_cv2.findContours.return_value = (["contour1"], None)
        mock_cv2.boundingRect.return_value = (10, 10, 100, 50)  # x, y, w, h
        mock_cv2.contourArea.return_value = 500  # Above min_area threshold
        mock_cv2.imencode.return_value = (True, Mock(tobytes=Mock(return_value=b"encoded_image")))
        
        # Mock Vision API response
        mock_response = Mock()
        mock_response.full_text_annotation.text = "OCR extracted text"
        mock_client.document_text_detection.return_value = mock_response
        
        pdf_file = Mock()
        pdf_file.read.return_value = b"fake pdf content"
        
        result = extract_highlights_or_fallback(pdf_file)
        
        # Should fall back to OCR
        mock_extract.assert_called_once()
        mock_vision.ImageAnnotatorClient.assert_called_once()
        mock_client.document_text_detection.assert_called_once()
        self.assertEqual(result, ["OCR extracted text"])


class FormsTestCase(TestCase):
    """Test cases for forms in core.forms module"""
    
    def test_pdf_upload_form_valid(self):
        """Test PDFUploadForm with valid PDF file"""
        # Create a mock PDF file
        pdf_content = b"fake pdf content"
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        
        form_data = {}
        form_files = {'pdf_file': pdf_file}
        form = PDFUploadForm(data=form_data, files=form_files)
        
        self.assertTrue(form.is_valid())
    
    def test_pdf_upload_form_no_file(self):
        """Test PDFUploadForm without file upload"""
        form = PDFUploadForm(data={}, files={})
        self.assertFalse(form.is_valid())
        self.assertIn('pdf_file', form.errors)
    
    def test_pdf_upload_form_widget_attributes(self):
        """Test that form widget has correct CSS class"""
        form = PDFUploadForm()
        widget_attrs = form.fields['pdf_file'].widget.attrs
        self.assertEqual(widget_attrs['class'], 'form-control w-100')
    
    def test_pdf_upload_form_label(self):
        """Test that form field has empty label"""
        form = PDFUploadForm()
        self.assertEqual(form.fields['pdf_file'].label, '')


class ViewsTestCase(TestCase):
    """Test cases for views in core.views module"""
    
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
    
    def test_upload_pdf_get_request(self):
        """Test upload_pdf view with GET request"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
    
    @patch('core.views.extract_highlights_or_fallback')
    def test_upload_pdf_post_valid_file(self, mock_extract):
        """Test upload_pdf view with valid PDF file"""
        mock_extract.return_value = ["Test highlight 1", "Test highlight 2"]
        
        pdf_content = b"fake pdf content"
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        
        response = self.client.post('/', {'pdf_file': pdf_file})
        
        self.assertEqual(response.status_code, 200)
        mock_extract.assert_called_once()
        
        # Check session was updated
        session = self.client.session
        self.assertEqual(session['highlights'], ["Test highlight 1", "Test highlight 2"])
    
    def test_upload_pdf_post_invalid_form(self):
        """Test upload_pdf view with invalid form data"""
        response = self.client.post('/', {})
        self.assertEqual(response.status_code, 200)
        # Should render form with errors
        self.assertContains(response, 'form')
    
    def test_connect_to_notion_redirect(self):
        """Test connect_to_notion view redirects to Notion OAuth"""
        with patch('core.views.NOTION_CLIENT_ID', 'test-client-id'):
            response = self.client.get('/connect/')
            
            self.assertEqual(response.status_code, 302)
            self.assertIn('api.notion.com/v1/oauth/authorize', response.url)
            self.assertIn('test-client-id', response.url)
    
    def test_oauth_callback_missing_code(self):
        """Test oauth_callback view with missing authorization code"""
        response = self.client.get('/oauth/callback/')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Missing authorization code.")
    
    @patch('core.views.requests.post')
    def test_oauth_callback_successful_auth(self, mock_post):
        """Test oauth_callback view with successful authentication"""
        # Mock successful OAuth response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'access_token': 'test-token'}
        mock_post.return_value = mock_response
        
        response = self.client.get('/oauth/callback/', {'code': 'test-auth-code'})
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')  # upload_pdf URL name resolves to '/'
        
        # Check session was updated
        session = self.client.session
        self.assertEqual(session['notion_token'], 'test-token')
    
    @patch('core.views.requests.post')
    def test_oauth_callback_failed_auth(self, mock_post):
        """Test oauth_callback view with failed authentication"""
        # Mock failed OAuth response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        response = self.client.get('/oauth/callback/', {'code': 'invalid-code'})
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content.decode(), "Failed to authenticate with Notion.")
    
    def test_send_to_notion_no_highlights(self):
        """Test send_to_notion view with no highlights in session"""
        response = self.client.post('/send/')
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')  # upload_pdf URL name resolves to '/'
        
        # Check error message was added
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("No highlights found", str(messages[0]))
    
    def test_send_to_notion_no_token(self):
        """Test send_to_notion view with no Notion token"""
        session = self.client.session
        session['highlights'] = ['Test highlight']
        session.save()
        
        response = self.client.post('/send/')
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/connect/')  # connect_to_notion URL name resolves to '/connect/'
        
        # Check error message was added
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Connect to Notion", str(messages[0]))
    
    @patch('core.views.Client')
    @patch('core.views.config')
    def test_send_to_notion_success(self, mock_config, mock_client_class):
        """Test send_to_notion view with successful Notion API call"""
        # Setup mocks
        mock_config.return_value = 'test-page-id'
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Setup session
        session = self.client.session
        session['highlights'] = ['Test highlight 1', 'Test highlight 2']
        session['notion_token'] = 'test-token'
        session.save()
        
        response = self.client.post('/send/')
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')  # upload_pdf URL name resolves to '/'
        
        # Verify Notion client was called correctly
        mock_client_class.assert_called_once_with(auth='test-token')
        mock_client.blocks.children.append.assert_called_once()
        
        # Check success message was added
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("sent to Notion", str(messages[0]))
    
    @patch('core.views.Client')
    @patch('core.views.config')
    def test_send_to_notion_api_error(self, mock_config, mock_client_class):
        """Test send_to_notion view with Notion API error"""
        # Setup mocks
        mock_config.return_value = 'test-page-id'
        mock_client = Mock()
        mock_client.blocks.children.append.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client
        
        # Setup session
        session = self.client.session
        session['highlights'] = ['Test highlight']
        session['notion_token'] = 'test-token'
        session.save()
        
        response = self.client.post('/send/')
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')  # upload_pdf URL name resolves to '/'
        
        # Check error message was added
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Error sending to Notion", str(messages[0]))
    
    def test_privacy_view(self):
        """Test privacy_view renders correctly"""
        response = self.client.get('/privacy/')
        self.assertEqual(response.status_code, 200)
    
    def test_terms_view(self):
        """Test terms_view renders correctly"""
        response = self.client.get('/terms/')
        self.assertEqual(response.status_code, 200)
    
    def test_send_to_notion_get_request(self):
        """Test send_to_notion view with GET request (should redirect)"""
        response = self.client.get('/send/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')


class IntegrationTestCase(TestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        self.client = Client()
    
    @patch('core.views.extract_highlights_or_fallback')
    def test_upload_workflow_with_highlights(self, mock_extract):
        """Test complete upload workflow when highlights are found"""
        mock_extract.return_value = ["Extracted highlight text"]
        
        pdf_content = b"fake pdf content"
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        
        # Upload PDF
        response = self.client.post('/', {'pdf_file': pdf_file})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Extracted highlight text")
        
        # Check session contains highlights
        session = self.client.session
        self.assertEqual(session['highlights'], ["Extracted highlight text"])
    
    @patch('core.views.extract_highlights_or_fallback')
    def test_upload_workflow_no_highlights(self, mock_extract):
        """Test complete upload workflow when no highlights are found"""
        mock_extract.return_value = []
        
        pdf_content = b"fake pdf content"
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        
        # Upload PDF
        response = self.client.post('/', {'pdf_file': pdf_file})
        
        self.assertEqual(response.status_code, 200)
        # Should not contain highlights section
        self.assertNotContains(response, "Extracted Highlights")
        
        # Check session contains empty highlights
        session = self.client.session
        self.assertEqual(session['highlights'], [])
    
    @patch('core.views.extract_highlights_or_fallback')
    @patch('core.views.Client')
    @patch('core.views.config')
    def test_full_workflow_upload_and_send(self, mock_config, mock_client_class, mock_extract):
        """Test complete workflow: upload PDF, connect to Notion, send highlights"""
        # Setup mocks
        mock_extract.return_value = ["Test highlight from PDF"]
        mock_config.return_value = 'test-page-id'
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Step 1: Upload PDF
        pdf_content = b"fake pdf content"
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        upload_response = self.client.post('/', {'pdf_file': pdf_file})
        
        self.assertEqual(upload_response.status_code, 200)
        self.assertContains(upload_response, "Test highlight from PDF")
        
        # Step 2: Simulate Notion OAuth (manually set token)
        session = self.client.session
        session['notion_token'] = 'test-oauth-token'
        session.save()
        
        # Step 3: Send to Notion
        send_response = self.client.post('/send/')
        
        self.assertEqual(send_response.status_code, 302)
        self.assertEqual(send_response.url, '/')
        
        # Verify Notion API was called
        mock_client_class.assert_called_once_with(auth='test-oauth-token')
        mock_client.blocks.children.append.assert_called_once()
        
        # Check success message
        messages = list(get_messages(send_response.wsgi_request))
        self.assertTrue(any("sent to Notion" in str(msg) for msg in messages))
