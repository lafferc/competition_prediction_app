from django import forms
from captcha.fields import ReCaptchaField
from allauth import account, socialaccount
from member.models import Profile
import logging

g_logger = logging.getLogger(__name__)


class SignUpForm(account.forms.SignupForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    captcha = ReCaptchaField()

    display_name_format = forms.ChoiceField(choices=Profile._meta.get_field('display_name_format').choices)
    cookie_consent = forms.ChoiceField(choices=Profile._meta.get_field('cookie_consent').choices)

    def clean(self):
        super(SignUpForm, self).clean()

        if (self.cleaned_data['first_name'] and self.cleaned_data['last_name'] 
            and self.cleaned_data['first_name'] == self.cleaned_data['last_name']
            and self.cleaned_data['first_name'][:-2] == self.cleaned_data['username']):
                g_logger.error("Bot detected: username: '{username}', first: '{first_name}', last: '{last_name}', email: '{email}'".format(**self.cleaned_data))
                raise forms.ValidationError("Bot detected")

    def save(self, request):
        user = super(SignUpForm, self).save(request)

        user.profile.display_name_format = self.cleaned_data['display_name_format']
        user.profile.cookie_consent = self.cleaned_data['cookie_consent']
        user.profile.save()

        return user


class SocialSignupForm(socialaccount.forms.SignupForm):
    display_name_format = forms.ChoiceField(choices=Profile._meta.get_field('display_name_format').choices)
    cookie_consent = forms.ChoiceField(choices=Profile._meta.get_field('cookie_consent').choices)

    def save(self, request):
        user = super(SocialSignupForm, self).save(request)

        user.profile.display_name_format = self.cleaned_data['display_name_format']
        user.profile.cookie_consent = self.cleaned_data['cookie_consent']
        user.profile.save()

        return user
