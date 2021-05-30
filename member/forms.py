from django import forms
from django.contrib.auth.models import User
from .models import Profile


class NameChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('user', 'dob', 'test_features_enabled')


class AnnouncementForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)
    test_email = forms.BooleanField(required=False, help_text="Test email (Send only to me)")
