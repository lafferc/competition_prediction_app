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

g_logger = logging.getLogger(__name__)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dob = models.DateField(null=True, blank=True)
    display_name_format = models.IntegerField(
        default=0,
        choices=((0, "Full Name"),
                 (1, "username"),
                 (2, "user_id")),
        help_text="This how other users will see your name displayed")
    social_display_name_format = models.IntegerField(
        choices=((0, "username"),
                 (1, "display name"),
                 (2, "social account username or username"),
                 (3, "social account username or display name")),
        default=2,
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
        if self.display_name_format == 0:
            name = "%s %s" % (self.user.first_name, self.user.last_name)
            if name == " ":
                name = self.user.username
            return name
        if self.display_name_format == 1:
            return "%s" % self.user.username
        if self.display_name_format == 2:
            return "user_%d" % self.user.pk

    def email_user(self, subject, message, new_comp=False, connection=None):
        if not self.user.email:
            g_logger.warn("User %s doesn't have a valid email" % self.get_name())
            return False
        if not self.can_receive_emails:
            return False
        if new_comp and not self.email_on_new_competition:
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
    organisation = models.ForeignKey(Organisation)
    tournament = models.ForeignKey(Tournament)
    participants = models.ManyToManyField(Participant)
    token_len = models.PositiveIntegerField(default=6)

    def __str__(self):
        return self.organisation.name

    class Meta:
        unique_together = ('tournament', 'organisation',)


class Ticket(models.Model):
    competition = models.ForeignKey(Competition)
    token = models.CharField(max_length=10, unique=True, blank=True)
    used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.pk is None:
            all_chars = string.ascii_uppercase + string.digits
            n = self.competition.token_len
            self.token = ''.join(random.SystemRandom().choice(all_chars) for _ in range(n))
        super(Ticket, self).save(*args, **kwargs)
