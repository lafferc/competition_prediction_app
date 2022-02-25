from django import forms
from django.contrib.auth.models import User
from .models import Profile
from competition.models import Tournament
from allauth.socialaccount.models import SocialApp


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
    tournament = forms.ModelChoiceField(queryset=Tournament.objects.filter(state=Tournament.ACTIVE), required=False)


class SocialProviderForm(forms.Form):
    social_provider = forms.ModelChoiceField(queryset=SocialApp.objects.all(), required=False)
