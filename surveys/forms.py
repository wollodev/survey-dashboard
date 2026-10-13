from django import forms

from .validators import validate_csv_upload


class UploadForm(forms.Form):
    file = forms.FileField(label="CSV file", validators=[validate_csv_upload])
    name = forms.CharField(label="Name (optional)", max_length=200, required=False)
