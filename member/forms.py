from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UsernameField
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


class UserMergeForm(forms.ModelForm):
    username = forms.ChoiceField()
    first_name = forms.ChoiceField(required=False)
    last_name = forms.ChoiceField(required=False)
    email = forms.ChoiceField(label="Primary Email")

    def add_choices(self, queryset):
        for field in self.fields.keys():
            self.fields[field].choices = [(value,value) for value in queryset.values_list(field, flat=True) if value]


    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

class ProfileMergeForm(forms.ModelForm):
    # display_name_format = forms.ChoiceField()

    def merge_values(self, queryset):
        pass

    class Meta:
        model = Profile
        exclude = ['user']
        # fields = ['username', 'first_name', 'last_name', 'email']

        # widgets = {
        #         'can_receive_emails': forms.CheckboxInput(attrs={'disabled': True}),
        #         'email_on_new_competition': forms.TextInput(attrs={'disabled': True}),
        #         }

