import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import PDFUploadForm
from .utils import extract_highlights
from notion_client import Client
from decouple import config
from django.http import HttpResponse

NOTION_CLIENT_ID = config("NOTION_CLIENT_ID")
NOTION_CLIENT_SECRET = config("NOTION_CLIENT_SECRET")
REDIRECT_URI = "https://hilite.onrender.com/oauth/callback/"
#REDIRECT_URI = "http://127.0.0.1:8000/oauth/callback/"



def privacy_view(request):
    return render(request, "core/privacy.html")

def terms_view(request):
    return render(request, "core/terms.html")

# Create your views here.
def upload_pdf(request):
    form = PDFUploadForm()
    highlights = request.session.get("highlights",None)
    token = request.session.get("notion_token", None)
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = request.FILES['pdf_file']
            highlights = extract_highlights(pdf_file) 
            request.session["highlights"] = highlights
            print("Extracted highlights:", highlights)
            
            return render(request, 'upload.html', {
                'form': form,
                'highlights': highlights,
                'messages': messages.get_messages(request),
                'token' : token,
            })       
        
    return render(request, "upload.html", {
        'form': form,
        'highlights': highlights,
        'token' : token,
    })       

def connect_to_notion(request):
    base_url = "https://api.notion.com/v1/oauth/authorize"
    params = {
        "client_id": NOTION_CLIENT_ID,
        "response_type": "code",
        "owner": "user",
        "redirect_uri": REDIRECT_URI,
    }
    url = f"{base_url}?" + "&".join([f"{k}={v}" for k, v in params.items()])
    return redirect(url)

def oauth_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponse("Missing authorization code.", status=400)

    token_url = "https://api.notion.com/v1/oauth/token"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    auth = (NOTION_CLIENT_ID, NOTION_CLIENT_SECRET)

    response = requests.post(token_url, json=data, auth=auth, headers=headers)
    if response.status_code != 200:
        return HttpResponse("Failed to authenticate with Notion.", status=500)

    token_data = response.json()
    access_token = token_data.get("access_token")
    request.session["notion_token"] = access_token
    return redirect("upload_pdf")
    

def send_to_notion(request):
    if request.method == "POST":
        highlights = request.session.get("highlights", [])
        token = request.session.get("notion_token")
        page_id = config("NOTION_PAGE_ID")
        if not highlights:
            messages.error(request, "No highlights found to send.")
            return redirect("upload_pdf")
        
        if not token:
            request.session["highlights"] = highlights
            messages.error(request, "Connect to Notion before sending highlights")
            return redirect("connect_to_notion")

        try:
            notion = Client(auth=token)  
            #page_id = config("NOTION_PAGE_ID") # Replace with your actual Notion page ID
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
                    