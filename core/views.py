from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import PDFUploadForm
from .utils import extract_highlights
from notion_client import Client
from decouple import config

#import tempfile

def privacy_view(request):
    return render(request, "core/privacy.html")

def terms_view(request):
    return render(request, "core/terms.html")

# Create your views here.
def upload_pdf(request):
    highlights = None
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = request.FILES['pdf_file']
            '''with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                for chunk in request.FILES['pdf_file'].chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name'''
            highlights = extract_highlights(pdf_file) 

            request.session["highlights"] = highlights
            print("Extracted highlights:", highlights)
            return render(request, 'upload.html', {'form': form, 'highlights': highlights})       
    else:
        form = PDFUploadForm()
    return render(request, "upload.html", {"form": form})       


def send_to_notion(request):
    if request.method == "POST":
        highlights = request.session.get("highlights", [])
        if not highlights:
            messages.error(request, "No highlights found to send.")
            return redirect("upload_pdf")

        try:
            notion = Client(auth=config("NOTION_TOKEN"))  # Replace with your actual token
            page_id = config("NOTION_PAGE_ID") # Replace with your actual Notion page ID

            blocks = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": h}
                            }
                        ]
                    }
                }
                for h in highlights
            ]

            notion.blocks.children.append(block_id=page_id, children=blocks)
            messages.success(request, "Highlights sent to Notion.")
        except Exception as e:
            messages.error(request, f"Error sending to Notion: {e}")

    return redirect("upload_pdf")
                    