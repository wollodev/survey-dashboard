from django import forms


class UploadForm(forms.Form):
    file = forms.FileField(label="CSV-Datei")
    name = forms.CharField(label="Name (optional)", max_length=200, required=False)

    def clean_file(self):
        file = self.cleaned_data["file"]
        if not file.name.lower().endswith(".csv"):
            raise forms.ValidationError("Bitte eine .csv-Datei hochladen.")
        return file
