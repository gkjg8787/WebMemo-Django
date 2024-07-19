from django import forms
from .models import MemoText


# フォーム定義
class CSVUploadForm(forms.ModelForm):
    csv_file = forms.FileField(label="CSVファイル")

    class Meta:
        model = MemoText
        fields = ["csv_file"]
