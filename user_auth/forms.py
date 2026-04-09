from django import forms
from .models import custom_user,user_profile, Application
from django.core.validators import RegexValidator, URLValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import custom_user, user_profile, Application, InternshipPost, CompanyProfile

class RegisterForm(forms.ModelForm):
    role = forms.ChoiceField(
    choices=custom_user.ROLE_CHOICES,
    widget=forms.Select(attrs={'class': 'form-control'})
    )

    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm password"
    )

    class Meta:
        model = custom_user
        fields = ['username', 'email', 'role', 'password', 'confirm_password']

    # ✅ Duplicate Email Validation
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if custom_user.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

    # ✅ Strong Password Validation
    def clean_password(self):
        password = self.cleaned_data.get("password")
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        return password

    # ✅ Password Match Check
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")

        return cleaned_data

    # ✅ Save With Hashed Password
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username=forms.CharField()
    password=forms.CharField(widget=forms.PasswordInput)

class ProfileUpdateForm(forms.ModelForm):

    contact_number = forms.CharField(
        max_length=10,
        min_length=10,
        validators=[RegexValidator(regex=r'^\d{10}$', message="Contact number must be exactly 10 digits.")],
        widget=forms.TextInput(attrs={'type': 'tel', 'pattern': r'\d{10}', 'title': 'Enter exactly 10 digits'})
    )
    class Meta:
        model=user_profile
        fields=['full_name', 'contact_number', 'gender', 'age', 'date_of_birth', 
                  'qualifications', 'skills', 'certificates', 'area_of_interest', 'profile_picture']
        
    def clean_certificates(self):
        certificates = self.cleaned_data.get("certificates")
        if certificates:
            allowed_extensions = (".pdf", ".doc", ".docx", ".jpg", ".png", ".zip")
            if not certificates.name.endswith(allowed_extensions):
                raise forms.ValidationError("Only PDF, DOC, DOCX, JPG, PNG, and ZIP files are allowed.")
        return certificates


class UsernameUpdateForm(forms.ModelForm):
    class Meta:
        model = custom_user
        fields = ['username']

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if custom_user.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username
    

class ApplicationForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=10,
        validators=[RegexValidator(regex=r'^\d{10}$', message="Phone number must be exactly 10 digits.")]
    )

    resume = forms.FileField(required=True)
    certificates = forms.FileField(required=False)

    company_name = forms.CharField(max_length=255, required=False)
    linkedin = forms.URLField(validators=[URLValidator()], required=False)
    github = forms.URLField(validators=[URLValidator()], required=False)

    class Meta:
        model = Application
        fields = ['full_name', 'email', 'phone', 'address', 'skills', 'experience', 'company_name', 'linkedin', 
                  'github','freshers','preferred_technology', 'internship_role', 'resume', 'certificates']

    def clean_resume(self):
        resume = self.cleaned_data.get("resume")
        allowed_extensions = (".pdf", ".doc", ".docx")
        if resume and not resume.name.endswith(allowed_extensions):
            raise forms.ValidationError("Only PDF, DOC, and DOCX files are allowed for resumes.")
        return resume

    def clean_certificates(self):
        certificates = self.cleaned_data.get("certificates")
        if certificates:
            allowed_extensions = (".pdf", ".doc", ".docx", ".jpg", ".png", ".zip", ".pptx")
            if not certificates.name.endswith(allowed_extensions):
                raise forms.ValidationError("Only PDF, DOC, DOCX, JPG, PNG, and ZIP files are allowed for certificates.")
        return certificates

from .models import InternshipPost

class InternshipPostForm(forms.ModelForm):
    class Meta:
        model = InternshipPost
        fields = ['company_name','internship_title', 'description', 'apply_url']
    
class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ['company_name', 'contact_email', 'contact_number', 'website', 'logo']