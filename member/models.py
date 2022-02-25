from django.contrib.auth.models import User
from django.core import mail
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
import smtplib
import string
import random
from competition.models import Tournament, Participant
from allauth.socialaccount.models import SocialAccount
from allauth.account.admin import EmailAddress

g_logger = logging.getLogger(__name__)


class Profile(models.Model):
    DNF_FULL = 0
    DNF_USR = 1
    DNF_ID = 2

    SDNF_USR = 0
    SDNF_DN = 1
    SDNF_SAU_USR = 2
    SDNF_SAU_DN = 3

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dob = models.DateField(null=True, blank=True)
    display_name_format = models.IntegerField(
        default=DNF_FULL,
        choices=((DNF_FULL, "Full Name"),
                 (DNF_USR, "username"),
                 (DNF_ID, "user_id")),
        help_text="This how other users will see your name displayed")
    social_display_name_format = models.IntegerField(
        choices=((SDNF_USR, "username"),
                 (SDNF_DN, "display name"),
                 (SDNF_SAU_USR, "social account username or username"),
                 (SDNF_SAU_DN, "social account username or display name")),
        default=SDNF_SAU_USR,
        help_text="This is how your name will be displayed on any 3rd party sites e.g. social media sites. Username is your username for this site. Display name is how your name is normally displayed on this site, format chosen by you. Social account username is the username of the social account you have linked to your account on this site.")
    can_receive_emails = models.BooleanField(
        default=True,
        help_text="Global email setting, if false the user will not receive any emails")
    email_on_new_competition = models.BooleanField(
        default=True,
        help_text="User will receive an email when new competitions are started")
    test_features_enabled = models.BooleanField(
        default=False,
        help_text="This user can use features that are under test")
    cookie_consent = models.PositiveIntegerField(
        default=0,
        choices=((0, "accept all cookies"),
                 (1, "no advertising cookies"),
                 (2, "functional cookies only")),
        help_text="The user consents to the following level of cookies")

    def get_name(self):
        if self.display_name_format == self.DNF_FULL:
            name = " ".join([self.user.first_name, self.user.last_name]).strip()
            return name or self.user.username
        if self.display_name_format == self.DNF_USR:
            return self.user.username
        if self.display_name_format == self.DNF_ID:
            return "user_%d" % self.user.pk

    def get_social_name(self, provider=None):
        if self.social_display_name_format == self.SDNF_USR:
            return self.user.username
        if self.social_display_name_format == self.SDNF_DN:
            return self.get_name()

        try:
            sa = SocialAccount.objects.get(user=self.user, provider=provider)
            name = sa.get_provider_account().to_str()
        except SocialAccount.DoesNotExist:
            name = None

        if self.social_display_name_format == self.SDNF_SAU_USR:
            return name or self.user.username
        if self.social_display_name_format == self.SDNF_SAU_DN:
            return name or self.get_name()

    def email_user(self, subject, message, new_comp=False, connection=None):
        if not self.user.email:
            return False
        if not self.user.is_active:
            return False
        if not self.can_receive_emails:
            return False
        if new_comp and not self.email_on_new_competition:
            return False
        if not EmailAddress.objects.filter(user=self.user, primary=True, verified=True).exists():
            return False
        try:
            if connection is None:
                self.user.email_user(subject, message)
            else:
                email = mail.EmailMessage(
                        subject,
                        message,
                        None,
                        [self.user.email],
                        connection=connection)
                email.send()
            return True
        except smtplib.SMTPRecipientsRefused:
            g_logger.error("Recipient Refused:'%s' (user: %s)",
                           self.user.email, self.user)
            return False

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Organisation(models.Model):
    name = models.CharField(max_length=50, unique=True)
    contact = models.CharField(max_length=50, blank=True)
    logo = models.ImageField(upload_to='images/', null=True, blank=True)

    def __str__(self):
        return self.name


class Competition(models.Model):
    organisation = models.ForeignKey(Organisation, models.CASCADE)
    tournament = models.ForeignKey(Tournament, models.CASCADE)
    participants = models.ManyToManyField(Participant)
    token_len = models.PositiveIntegerField(default=6)

    def __str__(self):
        return self.organisation.name

    class Meta:
        unique_together = ('tournament', 'organisation',)


class Ticket(models.Model):
    competition = models.ForeignKey(Competition, models.CASCADE)
    token = models.CharField(max_length=10, unique=True, blank=True)
    used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.pk is None:
            all_chars = string.ascii_uppercase + string.digits
            n = self.competition.token_len
            self.token = ''.join(random.SystemRandom().choice(all_chars) for _ in range(n))
        super(Ticket, self).save(*args, **kwargs)
