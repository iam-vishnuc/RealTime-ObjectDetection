from django import forms
from .models import Dataset,Register

class DatasetUploadForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['name', 'description', 'zip_file']



# class RegisterForm(forms.Form):
#     username = forms.CharField(max_length=50)
#     email = forms.EmailField()
#     password = forms.CharField(max_length=50)
#     confirm_password = forms.CharField(max_length=50)

#     def clean(self):
#         cleaned_data = super().clean()
#         password = cleaned_data.get("password")
#         confirm_password = cleaned_data.get("confirm_password")

#         if password and confirm_password and password != confirm_password:
#             raise forms.ValidationError("password do not match")
        
# class LoginForm(forms.Form):
#     username = forms.CharField(max_length=50)
#     password = forms.CharField(max_length=50)
