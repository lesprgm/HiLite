# HiLite

**HiLite** is a Django web application that extracts highlighted text from PDF documents and exports those highlights directly to your **Notion** workspace using the official Notion API via OAuth.

It simplifies the note-taking process for students, researchers, and professionals who annotate PDFs and want their insights organized in Notion without manual copy-pasting.

---

##  Features

-  Upload PDF documents via a clean and responsive web UI
-  Extract **highlighted text** automatically using PyMuPDF
-  Connect to Notion securely via OAuth 2.0
-  One-click export to your Notion page
-  Responsive Bootstrap 5 frontend with custom styling
-  No data stored — highlights live only in your session
-  Preview uploaded PDF highlights inside the app
-  Fallback to **OCR-based highlight detection** using Cloud Vision when needed( Uses a lot of memory so does not work in the web app unless you can help me with this)


---

## Important Considerations for OCR & Memory Usage (Fallback feature)
HiLite leverages Google Cloud Vision API for  OCR capabilities to extract text. While powerful, processing PDFs, especially large or high-DPI documents, is memory-intensive.

Memory Footprint: The OCR process can consume significant RAM. This application is optimized to reduce memory usage by processing one page at a time and using lower DPI settings for image conversion, but large PDFs (many pages, complex layouts, or very high resolution) may still strain server memory limits, particularly on free or lower-tier hosting plans (e.g., Render's free tier).

Performance: Processing time will vary based on PDF complexity, size, and your hosting environment's resources.

OCR Accuracy: Accuracy depends on the clarity of the text in the PDF and the quality of the OCR engine.


---

##  Folder Structure

```
hilite/
├── core/
│   ├── templates/
│   │   └── core/
│   │       ├── upload.html
│   │       ├── privacy.html
│   │       └── terms.html
│   ├── static/
│   │   └── core/
│   │       ├── styles.css
│   │       ├── script.js
│   │       └── highlighter.png
│   ├── views.py
│   ├── utils.py
│   └── forms.py
├── hilite_project/
│   ├── settings.py
│   ├── urls.py
├── manage.py
└── .env
```

---

##  Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/hilite.git
cd hilite
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Add Environment Variables

Create a `.env` file and add your secrets:

```ini
NOTION_CLIENT_ID=your_client_id
NOTION_CLIENT_SECRET=your_client_secret
NOTION_PAGE_ID=your_page_id
```

> ⚠ Make sure `.env` is listed in `.gitignore` to avoid pushing secrets to GitHub.


### 5. Apply Migrations

```bash
python manage.py migrate
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

Visit: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

##  Notion Integration (OAuth)

1. Go to [Notion Integrations](https://www.notion.com/my-integrations) and create a new integration.
2. Set the **redirect URI** to:

```
https://your-domain.com/oauth/callback/ (or http://127.0.0.1:8000/oauth/callback/ for local testing)
```

3. Save the **client ID** and **client secret** from Notion and add them to your `.env`.
4. Share your Notion page with your integration (click "Share" → "Invite" → choose your integration).
5. Copy the **Notion page ID** from the URL and include it in `.env`.

---

##  UI Preview

The app includes:

- Gradient background and branding
- PDF upload form
- Live extracted highlights list
- Connect to Notion button
- Export to Notion button (shown only after uploading)

---

##  Requirements

Add this to your `requirements.txt`:

```
Django>=5.2.1
notion-client>=2.3.0
PyMuPDF>=1.26.0
python-decouple>=3.8
opencv-python-headless==4.9.0.80
pdf2image==1.17.0
google-cloud-vision>=3.4.0 # For Google Cloud Vision API

```

---

##  Future Enhancements

- User authentication and session tracking
- Dynamic Notion page selection and creation
- Drag-and-drop file upload
- Batch export support for multiple PDFs
- Ability to extract other annotations from documents

---

##  License

MIT License — free to use, modify, and distribute.

---

##  Author

Built by **Leslie Osei-Anane**.
