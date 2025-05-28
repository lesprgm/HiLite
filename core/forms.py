from django import forms

class PDFUploadForm(forms.Form):
    pdf_file = forms.FileField(label = '')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['pdf_file'].widget.attrs.update({
            'class': 'form-control w-100'
        })
