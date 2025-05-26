# HiLite 

**HiLite** is a Django web application that extracts highlighted text from PDF documents and sends those highlights directly to your **Notion** workspace using the official Notion API.

It streamlines the note-taking process for students, researchers, and professionals who annotate PDFs and want their key insights stored in Notion.

---

## Features

-  Upload PDF documents via a sleek web interface
-  Automatically extract **highlighted text** using PyMuPDF
-  One-click export to a Notion page
-  Clean, responsive UI styled with Bootstrap 5
-  Secure Notion API integration using `notion-client`

---

## Folder Structure

```
hilite/
├── core/
│   ├── templates/
│   │   └── core/
│   │       └── upload.html
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
└── README.md
```

---

## Setup Instructions

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

### 4. Apply Migrations

```bash
python manage.py migrate
```

### 5. Run the Server

```bash
python manage.py runserver
```

Open your browser and visit: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Notion Integration Setup

1. Go to [Notion Integrations](https://www.notion.com/my-integrations) and create a new integration.
2. Copy the integration **token**.
3. Share a Notion page with the integration (using the “Share” → “Invite” button).
4. Copy the **page ID** from the Notion page URL.
5. In your `views.py`, replace:

```python
notion = Client(auth="your_notion_token")
page_id = "your_page_id"
```

> Tip: You can store these securely using environment variables and `python-decouple`.

---

##  UI Preview

The landing page includes:

- A gradient background
- Custom highlighter icon
- PDF upload form
- Extracted highlights display
- A "Send to Notion" button that only appears after upload

---

## Requirements

Add this to your `requirements.txt` if you haven't already:

```
Django>=5.2
notion-client>=2.2.1
PyMuPDF>=1.23.22
```

---

## Future Enhancements

- User authentication
- Let users select or create Notion pages dynamically
- Drag-and-drop PDF upload
- In-app PDF highlight preview
- Export multiple files at once

---

## License

MIT License — free to use, modify, and distribute.

---

## Author

Built by **Leslie Osei-Anane**.
