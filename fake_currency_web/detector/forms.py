from django import forms
from .models import Prediction

class UploadForm(forms.ModelForm):
    class Meta:
        model = Prediction
        fields = ['image']