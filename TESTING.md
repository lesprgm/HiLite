# Testing Documentation

This document describes the comprehensive test suite for the HiLite application.

## Test Coverage

The test suite covers all major functionality areas:

### 📁 UtilsTestCase (core/utils.py)
- **Text cleaning**: Tests for the `clean_text()` function including edge cases
- **PDF highlight extraction**: Tests for `extract_highlights()` with mocked PyMuPDF
- **OCR fallback**: Tests for `extract_highlights_or_fallback()` including Google Cloud Vision API integration

### 📁 FormsTestCase (core/forms.py)  
- **Form validation**: Tests for `PDFUploadForm` with valid and invalid inputs
- **Widget attributes**: Tests for CSS classes and form attributes

### 📁 ViewsTestCase (core/views.py)
- **Upload workflow**: Tests for PDF upload handling
- **OAuth flow**: Tests for Notion OAuth integration
- **API integration**: Tests for sending highlights to Notion
- **Error handling**: Tests for various error scenarios
- **Privacy/Terms pages**: Tests for static page views

### 📁 IntegrationTestCase
- **End-to-end workflows**: Complete user journeys from upload to Notion export
- **Session management**: Tests for highlight persistence in user sessions

## Running Tests

### Run all tests:
```bash
python manage.py test core.tests
```

### Run with verbose output:
```bash
python manage.py test core.tests --verbosity=2
```

### Run specific test class:
```bash
python manage.py test core.tests.UtilsTestCase
```

### Run specific test method:
```bash
python manage.py test core.tests.UtilsTestCase.test_clean_text_basic
```

## Test Features

- **Mocked external dependencies**: All tests run without requiring actual API calls
- **Comprehensive coverage**: Tests cover happy paths, error cases, and edge conditions
- **Django integration**: Proper use of Django test client and database
- **Isolated tests**: Each test is independent and can run in any order

## Adding New Tests

When adding new functionality:

1. Add unit tests for new utility functions in `UtilsTestCase`
2. Add form tests for new forms in `FormsTestCase`  
3. Add view tests for new views/endpoints in `ViewsTestCase`
4. Add integration tests for new user workflows in `IntegrationTestCase`

## Test Dependencies

The tests use Python's built-in `unittest.mock` library to mock external dependencies:

- **PyMuPDF (fitz)**: Mocked for PDF processing
- **Google Cloud Vision**: Mocked for OCR functionality
- **Notion API**: Mocked for Notion integration
- **File uploads**: Uses Django's `SimpleUploadedFile` for testing

This ensures tests run quickly and don't require external services.