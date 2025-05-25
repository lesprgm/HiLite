from django.shortcuts import render
from .forms import PDFUploadForm
from .utils import extract_highlights
import tempfile

# Create your views here.
def upload_pdf(request):
    highlights = None
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                for chunk in request.FILES['pdf_file'].chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            highlights = extract_highlights(tmp_path)
            print("Extracted highlights:", highlights)

            
    else:
        form = PDFUploadForm
        
    return render(request, 'upload.html', {'form': form, 'highlights': highlights})
                    