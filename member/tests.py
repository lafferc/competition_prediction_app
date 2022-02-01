from django.contrib.auth.models import User, Permission
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase

import unittest

from .models import Organisation, Competition, Ticket
from competition.models import Tournament, Sport, Participant


class MemberViewLoggedOutTest(TestCase):
    fixtures = ['social.json']

    @classmethod
    def setUpTestData(cls):
        cls.url_login_next = reverse('account_login') + "?next="

    def test_profile(self):
        url = reverse('member:profile')
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_use_token(self):
        url = reverse('member:use_token')
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_announcement(self):
        url = reverse('member:announcement')
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_tickets(self):
        url = reverse('member:tickets', kwargs={'comp_pk': 1})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)


class MemberViewTest(TestCase):
    fixtures = ['social.json']

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser1', password='test123')
        cls.user.save()
        cls.url_login_next = reverse('account_login') + "?next="

        sport = Sport.objects.create(name='sport')
        cls.tourn = Tournament.objects.create(name='active_tourn', sport=sport, state=Tournament.ACTIVE)
        with open('member/test_logo.png', 'rb') as rawfile:
            logo = SimpleUploadedFile('logo.png', content=rawfile.read())
        cls.org = Organisation.objects.create(name="Test", logo=logo)
        cls.comp = Competition.objects.create(organisation=cls.org, tournament=cls.tourn)
        cls.ticket = Ticket.objects.create(competition=cls.comp)

    def setUp(self):
        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)

    def test_profile(self):
        url = reverse('member:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')

    def test_profile_update(self):
        self.assertEqual(self.user.profile.get_name(), 'testuser1')
        url = reverse('member:profile')
        response = self.client.post(url, {
            'first_name': 'Test1',
            'last_name': 'User',
            'display_name_format': 0,
            'social_display_name_format': 0,
            'can_receive_emails': 1,
            'email_on_new_competition': 1,
            'cookie_consent': 0,
        })
        self.assertRedirects(response, url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.get_name(), 'Test1 User')

        response = self.client.post(url, {
            'display_name_format': 1,
            'social_display_name_format': 0,
            'can_receive_emails': 1,
            'email_on_new_competition': 1,
            'cookie_consent': 0,
        })
        self.assertRedirects(response, url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.get_name(), 'testuser1')

        response = self.client.post(url, {
            'display_name_format': 2,
            'social_display_name_format': 0,
            'can_receive_emails': 1,
            'email_on_new_competition': 1,
            'cookie_consent': 0,
        })
        self.assertRedirects(response, url)

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.get_name(), 'user_1')

    def test_use_token(self):
        url = reverse('member:use_token')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'token.html')

    def test_use_token_post(self):
        url = reverse('member:use_token')
        r_url = reverse('competition:org_table', kwargs={'slug': self.tourn.slug,
                                                         'org_name': self.org.name})
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.used)
        count_before = len(Participant.objects.filter(tournament=self.tourn))

        response = self.client.post(url, {
            'token': self.ticket.token,
        })
        self.assertRedirects(response, r_url)

        count_after = len(Participant.objects.filter(tournament=self.tourn))
        self.assertEqual(count_after, count_before + 1)

        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.used)

    def test_use_token_participant_post(self):
        url = reverse('member:use_token')
        r_url = reverse('competition:org_table', kwargs={'slug': self.tourn.slug,
                                                         'org_name': self.org.name})
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.used)
        Participant.objects.create(user=self.user, tournament=self.tourn)

        count_before = len(Participant.objects.filter(tournament=self.tourn))

        response = self.client.post(url, {
            'token': self.ticket.token,
        })
        self.assertRedirects(response, r_url)

        count_after = len(Participant.objects.filter(tournament=self.tourn))
        self.assertEqual(count_after, count_before)

        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.used)

    def test_announcement(self):
        url = reverse('member:announcement')
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        self.user.is_superuser = True
        self.user.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement.html')

    def test_announcement_post(self):
        url = reverse('member:announcement')
        response = self.client.post(url, {
            'subject': "Test",
            'message': "body",
        })
        self.assertRedirects(response, self.url_login_next + url)

    def test_tickets(self):
        comp = Competition.objects.get(organisation__name="Test")
        url = reverse('member:tickets', kwargs={'comp_pk': comp.pk})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets.html')

class AnnouncementTest(TestCase):
    fixtures = ['social.json', 'accounts.json']

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(username='testuser1')
        cls.user.set_password("test123")
        cls.user.is_superuser = True
        cls.user.save()

        user = User.objects.get(username='cant-receive-emails')
        user.profile.can_receive_emails = False
        user.profile.save()

        cls.url = reverse('member:announcement')

    def setUp(self):
        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)

    def test_announcement_test_email(self):
        response = self.client.post(self.url, {
            'subject': "Test subject",
            'message': "test email body",
            'test_email': "true",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement_sent.html')

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEqual(email.subject, "Test subject")
        self.assertEqual(email.to, ['testuser1@example.com'])

        self.assertTrue("test email body" in email.body)

    def test_announcement_email(self):
        excluded_users = ['blankemail', 'unverified', 'cant-receive-emails', 'inactive']
        expected_emails = User.objects.exclude(username__in=excluded_users).values_list('email', flat=True)

        response = self.client.post(self.url, {
            'subject': "Test subject",
            'message': "test email body",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement_sent.html')
        self.assertEqual(response.context['user_list_len'], len(expected_emails))

        self.assertEqual(len(mail.outbox), len(expected_emails))
        self.assertEqual(set([e.to[0] for e in mail.outbox]), set(expected_emails))
        email = mail.outbox[0]

        self.assertEqual(email.subject, "Test subject")

        self.assertTrue("test email body" in email.body)

    def test_announcement_email_tourn(self):
        sport = Sport.objects.create(name='sport')
        tourn = Tournament.objects.create(name='active_tourn', sport=sport, state=Tournament.ACTIVE)

        excluded_users = ['blankemail', 'unverified', 'inactive']
        for user in User.objects.exclude(username__in=excluded_users):
            Participant.objects.create(user=user, tournament=tourn)

        expected_emails = tourn.participants.exclude(username__in=['cant-receive-emails']).values_list('email', flat=True)

        response = self.client.post(self.url, {
            'subject': "Test subject",
            'message': "test email body",
            'tournament': tourn.pk,
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement_sent.html')

        self.assertEqual(response.context['user_list_len'], len(expected_emails))
        self.assertEqual(len(mail.outbox), len(expected_emails))
        self.assertEqual(set([e.to[0] for e in mail.outbox]), set(expected_emails))

        email = mail.outbox[0]
        self.assertEqual(email.subject, "Test subject")
        self.assertTrue("test email body" in email.body)
