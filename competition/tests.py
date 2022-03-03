from django.contrib.auth.models import User, Permission
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.db.models.signals import pre_save

import datetime
import pytz
import unittest
from decimal import Decimal
import string

from .models import Sport, Tournament, Participant
from .models import Benchmark, Team, Match, Prediction

class CompetitionViewLoggedOutTest(TestCase):
    fixtures = ['social.json']

    @classmethod
    def setUpTestData(cls):
        cls.url_login_next = reverse('account_login') + "?next="

    def test_index(self):
        url = reverse('competition:index')
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_predictions(self):
        url = reverse('competition:predictions', kwargs={'slug':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_table(self):
        url = reverse('competition:table', kwargs={'slug':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_org_table(self):
        url = reverse('competition:org_table', kwargs={'slug':'tourn', 'org_name': 'org'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_join(self):
        url = reverse('competition:join', kwargs={'slug':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_results(self):
        url = reverse('competition:results', kwargs={'slug':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_rules(self):
        url = reverse('competition:rules', kwargs={'slug':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_match(self):
        url = reverse('competition:match', kwargs={'match_pk':1})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_benchmark_table(self):
        url = reverse('competition:benchmark_table', kwargs={'slug':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_benchmark(self):
        url = reverse('competition:benchmark', kwargs={'benchmark_pk': 1})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)


class CompetitionViewNotParticipantTest(TestCase):
    fixtures = ['social.json']

    @classmethod
    def setUpTestData(cls):
        #print("setUpTestData: Run once to set up non-modified data for all class methods.")
        test_user1 = User.objects.create_user(username='testuser1', password='test123')
        test_user1.save()
        test_user2 = User.objects.create_user(username='testuser2', password='test123')
        test_user2.save()

        sport = Sport.objects.create(name='sport')
        for state, name in Tournament._meta.get_field('state').choices:
            # print("creating %s_tourn" % name.lower())
            Tournament.objects.create(name='%s_tourn' % name.lower(), sport=sport, state=state)

        cls.url_login_next = reverse('account_login') + "?next="

    def setUp(self):
        #print("setUp: Run once for every test method to setup clean data.")
        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)

    def tearDown(self):
        #print("tearDown: Run after every test method")
        pass

    def test_index(self):
        response = self.client.get(reverse('competition:index'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        # Check we used correct template
        self.assertTemplateUsed(response, 'index.html')

    def test_submit_pending(self):
        url = reverse('competition:submit', kwargs={'slug':'pending_tourn'})
        join_url = reverse('competition:join', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, join_url)

    def test_submit_active(self):
        url = reverse('competition:submit', kwargs={'slug':'active_tourn'})
        join_url = reverse('competition:join', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, join_url)

    def test_submit_finished(self):
        url = reverse('competition:submit', kwargs={'slug':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_submit_archived(self):
        url = reverse('competition:submit', kwargs={'slug':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_predictions_pending(self):
        url = reverse('competition:predictions', kwargs={'slug':'pending_tourn'})
        r_url = reverse('competition:join', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, r_url)

    def test_predictions_active(self):
        url = reverse('competition:predictions', kwargs={'slug':'active_tourn'})
        r_url = reverse('competition:join', kwargs={'slug':'active_tourn'})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, r_url)

    def test_predictions_finished(self):
        url = reverse('competition:predictions', kwargs={'slug':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_predictions_archived(self):
        url = reverse('competition:predictions', kwargs={'slug':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_table_pending(self):
        url = reverse('competition:table', kwargs={'slug':'pending_tourn'})
        r_url = reverse('competition:join', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_table_active(self):
        url = reverse('competition:table', kwargs={'slug':'active_tourn'})
        r_url = reverse('competition:join', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_table_finished(self):
        url = reverse('competition:table', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_table_archived(self):
        url = reverse('competition:table', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_join_pending(self):
        url = reverse('competition:join', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join.html')

        count_before = len(Participant.objects.filter(tournament__name='pending_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='pending_tourn'))
        self.assertEqual(count_after, count_before + 1)

        r_url = reverse('competition:submit', kwargs={'slug':'pending_tourn'})
        self.assertRedirects(response, r_url)

    def test_join_active(self):
        url = reverse('competition:join', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join.html')

        count_before = len(Participant.objects.filter(tournament__name='active_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='active_tourn'))
        self.assertEqual(count_after, count_before + 1)

        r_url = reverse('competition:submit', kwargs={'slug':'active_tourn'})
        self.assertRedirects(response, r_url)

    def test_join_finished(self):
        url = reverse('competition:join', kwargs={'slug':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)
        count_before = len(Participant.objects.filter(tournament__name='finished_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='finished_tourn'))
        self.assertEqual(count_after, count_before)

        self.assertRedirects(response, r_url)

    def test_join_archived(self):
        url = reverse('competition:join', kwargs={'slug':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

        count_before = len(Participant.objects.filter(tournament__name='archived_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='archived_tourn'))
        self.assertEqual(count_after, count_before)

        self.assertRedirects(response, r_url)

    def test_results_pending(self):
        url = reverse('competition:results', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_active(self):
        url = reverse('competition:results', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_finished(self):
        url = reverse('competition:results', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_archived(self):
        url = reverse('competition:results', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_rules_pending(self):
        url = reverse('competition:rules', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_rules_active(self):
        url = reverse('competition:rules', kwargs={'slug':'active_tourn'})
        r_url = reverse('competition:join', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_rules_finished(self):
        url = reverse('competition:rules', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_rules_archived(self):
        url = reverse('competition:rules', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

#     def test_match_pending(self):
#     def test_match_active(self):
#     def test_match_finished(self):
#     def test_match_archived(self):
# 
    def test_benchmark_table_pending(self):
        url = reverse('competition:benchmark_table', kwargs={'slug':'pending_tourn'})
        r_url = reverse('competition:join', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_benchmark_table_active(self):
        url = reverse('competition:benchmark_table', kwargs={'slug':'active_tourn'})
        r_url = reverse('competition:join', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_benchmark_table_finished(self):
        url = reverse('competition:benchmark_table', kwargs={'slug':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, r_url)

    def test_benchmark_table_archived(self):
        url = reverse('competition:benchmark_table', kwargs={'slug':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, r_url)


class CompetitionViewTest(TestCase):
    fixtures = ['social.json']

    @classmethod
    def setUpTestData(cls):
        #print("setUpTestData: Run once to set up non-modified data for all class methods.")
        test_user1 = User.objects.create_user(username='testuser1', password='test123')
        test_user1.save()
        test_user2 = User.objects.create_user(username='testuser2', password='test123')
        test_user2.save()

        sport = Sport.objects.create(name='sport')
        team_a = Team.objects.create(name='team A', code='AAA', sport=sport)
        team_b = Team.objects.create(name='team B', code='BBB', sport=sport)
        tomorrow = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(days=1)
        for state, name in Tournament._meta.get_field('state').choices:
            tourn = Tournament.objects.create(name='%s_tourn' % name.lower(),
                                              sport=sport,
                                              state=state,
                                              test_features_enabled=True)
            Match.objects.create(tournament=tourn, home_team=team_a, away_team=team_b, kick_off=tomorrow)
            Participant.objects.create(user=test_user1, tournament=tourn)
            Benchmark.objects.create(tournament=tourn, name="all draws",
                                     prediction_algorithm=Benchmark.STATIC,
                                     static_value=0)

        cls.url_login_next = reverse('account_login') + "?next="

    def setUp(self):
        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)

    def test_index(self):
        url = reverse('competition:index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_submit_pending(self):
        url = reverse('competition:submit', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'submit.html')

    def test_submit_active(self):
        url = reverse('competition:submit', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'submit.html')

    def test_submit_finished(self):
        url = reverse('competition:submit', kwargs={'slug':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_submit_archived(self):
        url = reverse('competition:submit', kwargs={'slug':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_predictions_pending(self):
        url = reverse('competition:predictions', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_predictions_active(self):
        url = reverse('competition:predictions', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_predictions_finished(self):
        url = reverse('competition:predictions', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_predictions_archived(self):
        url = reverse('competition:predictions', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_table_pending(self):
        url = reverse('competition:table', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_table_active(self):
        url = reverse('competition:table', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_table_finished(self):
        url = reverse('competition:table', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_table_archived(self):
        url = reverse('competition:table', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    @unittest.skip("transaction error")
    def test_join_pending(self):
        url = reverse('competition:join', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join.html')

        count_before = len(Participant.objects.filter(tournament__name='pending_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='pending_tourn'))
        self.assertEqual(count_after, count_before)

        r_url = reverse('competition:submit', kwargs={'slug':'pending_tourn'})
        self.assertRedirects(response, r_url)

    @unittest.skip("transaction error")
    def test_join_active(self):
        url = reverse('competition:join', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join.html')

        count_before = len(Participant.objects.filter(tournament__name='active_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='active_tourn'))
        self.assertEqual(count_after, count_before)

        r_url = reverse('competition:submit', kwargs={'slug':'active_tourn'})
        self.assertRedirects(response, r_url)

    def test_join_finished(self):
        url = reverse('competition:join', kwargs={'slug':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)
        count_before = len(Participant.objects.filter(tournament__name='finished_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='finished_tourn'))
        self.assertEqual(count_after, count_before)

        self.assertRedirects(response, r_url)

    def test_join_archived(self):
        url = reverse('competition:join', kwargs={'slug':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

        count_before = len(Participant.objects.filter(tournament__name='archived_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='archived_tourn'))
        self.assertEqual(count_after, count_before)

        self.assertRedirects(response, r_url)

    def test_results_pending(self):
        url = reverse('competition:results', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_active(self):
        url = reverse('competition:results', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_finished(self):
        url = reverse('competition:results', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_archived(self):
        url = reverse('competition:results', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_rules_pending(self):
        url = reverse('competition:rules', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_rules_active(self):
        url = reverse('competition:rules', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_rules_finished(self):
        url = reverse('competition:rules', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_rules_archived(self):
        url = reverse('competition:rules', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_match_pending(self):
        match = Match.objects.filter(tournament__name='pending_tourn')[0]
        url = reverse('competition:match', kwargs={'match_pk': match.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match.html')

    def test_match_active(self):
        match = Match.objects.filter(tournament__name='active_tourn')[0]
        url = reverse('competition:match', kwargs={'match_pk': match.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match.html')

    def test_match_finished(self):
        match = Match.objects.filter(tournament__name='finished_tourn')[0]
        url = reverse('competition:match', kwargs={'match_pk': match.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match.html')

    def test_match_archived(self):
        match = Match.objects.filter(tournament__name='archived_tourn')[0]
        url = reverse('competition:match', kwargs={'match_pk': match.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match.html')


    def test_benchmark_table_pending(self):
        url = reverse('competition:benchmark_table', kwargs={'slug':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_benchmark_table_active(self):
        url = reverse('competition:benchmark_table', kwargs={'slug':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_benchmark_table_finished(self):
        url = reverse('competition:benchmark_table', kwargs={'slug':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_benchmark_table_archived(self):
        url = reverse('competition:benchmark_table', kwargs={'slug':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_benchmark_pending(self):
        benchmark = Benchmark.objects.filter(tournament__name='pending_tourn')[0]
        url = reverse('competition:benchmark', kwargs={'benchmark_pk': benchmark.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_benchmark_active(self):
        benchmark = Benchmark.objects.filter(tournament__name='active_tourn')[0]
        url = reverse('competition:benchmark', kwargs={'benchmark_pk': benchmark.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_benchmark_finished(self):
        benchmark = Benchmark.objects.filter(tournament__name='finished_tourn')[0]
        url = reverse('competition:benchmark', kwargs={'benchmark_pk': benchmark.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_benchmark_archived(self):
        benchmark = Benchmark.objects.filter(tournament__name='archived_tourn')[0]
        url = reverse('competition:benchmark', kwargs={'benchmark_pk': benchmark.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')


class HomePageContent(TestCase):
    fixtures = ['social.json']

    @classmethod
    def setUpTestData(cls):
        sport = Sport.objects.create(name='sport')
        tourn_a = Tournament.objects.create(name='tourn_A',
                                            sport=sport,
                                            state=Tournament.ACTIVE)
        tourn_b = Tournament.objects.create(name='tourn_B',
                                            sport=sport,
                                            state=Tournament.ACTIVE)
        tourn_c = Tournament.objects.create(name='tourn_C',
                                  sport=sport,
                                  state=Tournament.ACTIVE)
        Tournament.objects.create(name='tourn_D',
                                  sport=sport,
                                  state=Tournament.FINISHED)

        cls.tourns = [tourn_a, tourn_b, tourn_c]
        cls.user = User.objects.create_user(username='testuser1', password='test123')
        cls.user.save()

        Participant.objects.create(user=cls.user, tournament=tourn_a)
        Participant.objects.create(user=cls.user, tournament=tourn_b)

        cls.team_a = Team.objects.create(name='team A', code='AAA', sport=sport)
        cls.team_b = Team.objects.create(name='team B', code='BBB', sport=sport)

        today = timezone.make_aware(datetime.datetime.combine(datetime.date.today(), datetime.time()))

        cls.times_today = [
            today + datetime.timedelta(hours=6),
            today + datetime.timedelta(hours=12),
            today + datetime.timedelta(hours=18),
        ]
        cls.times_tomorrow = [
            today + datetime.timedelta(days=1, hours=6),
            today + datetime.timedelta(days=1, hours=12),
            today + datetime.timedelta(days=1, hours=18),
        ]


    def setUp(self):
        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)

    def test_live_tournaments(self):
        response = self.client.get(reverse('competition:tournament_list_open'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/tournament_list_open.html')

        self.assertEqual(len(response.context['live_tournaments']), 3)

    def test_closed_tournaments(self):
        response = self.client.get(reverse('competition:tournament_list_closed'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/tournament_list_closed.html')

        self.assertEqual(len(response.context['closed_tournaments']), 1)

    def test_todays_matches(self):
        for tourn in self.tourns:
            for time in self.times_today:
                Match.objects.create(tournament=tourn, home_team=self.team_a, away_team=self.team_b, kick_off=time)

        response = self.client.get(reverse('competition:match_list_todaytomorrow'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/match_list_todaytomorrow.html')

        self.assertEqual(len(response.context['matches_today']), 6)
        self.assertEqual(len(response.context['matches_tomorrow']), 0)

    def test_tomorrows_matches(self):
        for tourn in self.tourns:
            for time in self.times_tomorrow:
                Match.objects.create(tournament=tourn, home_team=self.team_a, away_team=self.team_b, kick_off=time)

        response = self.client.get(reverse('competition:match_list_todaytomorrow'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/match_list_todaytomorrow.html')

        self.assertEqual(len(response.context['matches_today']), 0)
        self.assertEqual(len(response.context['matches_tomorrow']), 6)

    def test_today_and_tomorrows_matches(self):
        for tourn in self.tourns:
            for time in self.times_today + self.times_tomorrow:
                Match.objects.create(tournament=tourn, home_team=self.team_a, away_team=self.team_b, kick_off=time)

        response = self.client.get(reverse('competition:match_list_todaytomorrow'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/match_list_todaytomorrow.html')

        self.assertEqual(len(response.context['matches_today']), 6)
        self.assertEqual(len(response.context['matches_tomorrow']), 6)

    def test_no_matches_today_or_tomorrows(self):
        response = self.client.get(reverse('competition:match_list_todaytomorrow'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/match_list_todaytomorrow.html')

        self.assertEqual(len(response.context['matches_today']), 0)
        self.assertEqual(len(response.context['matches_tomorrow']), 0)



class PredictionsAndMatches(TransactionTestCase):
    fixtures = ['social.json']

    def setUp(self):
        self.user = User.objects.create_user(username='testuser1', password='test123')
        self.user.save()
        self.other_user = User.objects.create_user(username='testuser2', password='test123')
        self.other_user.save()

        sport = Sport.objects.create(name='sport')
        self.tourn = Tournament.objects.create(name='tourn',
                                            sport=sport,
                                            state=Tournament.ACTIVE)

        Participant.objects.create(user=self.user, tournament=self.tourn)
        Participant.objects.create(user=self.other_user, tournament=self.tourn)

        Benchmark.objects.create(tournament=self.tourn, name="rand", prediction_algorithm=Benchmark.RANDOM, range_start=-5, range_end=5)

        self.team_a = Team.objects.create(name='team A', code='AAA', sport=sport)
        self.team_b = Team.objects.create(name='team B', code='BBB', sport=sport)

        now = timezone.make_aware(datetime.datetime.now())

        self.matches = [
            Match.objects.create(pk=1, tournament=self.tourn, home_team=self.team_a, away_team=self.team_b, kick_off=now - datetime.timedelta(days=1, minutes=15)),
            Match.objects.create(pk=2, tournament=self.tourn, home_team=self.team_a, away_team=self.team_b, kick_off=now),
            Match.objects.create(pk=3, tournament=self.tourn, home_team=self.team_a, away_team=self.team_b, kick_off=now + datetime.timedelta(minutes=15)),
            Match.objects.create(pk=4, tournament=self.tourn, home_team=self.team_a, away_team=self.team_b, kick_off=now + datetime.timedelta(days=1, minutes=15)),
            Match.objects.create(pk=5, tournament=self.tourn, home_team=self.team_a, away_team=self.team_b, kick_off=now + datetime.timedelta(days=2)),
        ]

        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)

    def test_submit(self):
        url = reverse('competition:submit', kwargs={'slug':self.tourn.name})

        response = self.client.get(url)
        self.assertEqual(len(response.context['fixture_list']), 3)
        self.assertEqual(response.context['fixture_list'][0].pk, 3)

        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 0)

        response = self.client.post(
                reverse('competition:prediction_create', kwargs={'match_pk': 3}),
                { 'prediction_prediction': -3})
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url)
        self.assertEqual(len(response.context['fixture_list']), 2)
        self.assertEqual(response.context['fixture_list'][0].pk, 4)

        predictions = Prediction.objects.filter(match__pk=1, user=self.user)
        self.assertEqual(len(predictions), 0)
        predictions = Prediction.objects.filter(match__pk=2, user=self.user)
        self.assertEqual(len(predictions), 0)
        predictions = Prediction.objects.filter(match__pk=3, user=self.user)
        self.assertEqual(len(predictions), 1)
        self.assertEqual(predictions[0].prediction, -3)
        predictions = Prediction.objects.filter(match__pk=4, user=self.user)
        self.assertEqual(len(predictions), 0)

        response = self.client.post(
                reverse('competition:prediction_create', kwargs={'match_pk': 4}),
                { 'prediction_prediction': 4})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/messages.html')

        response = self.client.get(url)
        self.assertEqual(len(response.context['fixture_list']), 1)

        predictions = Prediction.objects.filter(match__pk=3, user=self.user)
        self.assertEqual(len(predictions), 1)
        self.assertEqual(predictions[0].prediction, -3)
        self.assertFalse(predictions[0].late)
        predictions = Prediction.objects.filter(match__pk=4, user=self.user)
        self.assertEqual(len(predictions), 1)
        self.assertEqual(predictions[0].prediction, 4)

    def test_predictions(self):
        url = reverse('competition:predictions', kwargs={'slug': self.tourn.name})

        p1 = Prediction.objects.create(match=self.matches[0], prediction=1, user=self.user)
        p2 = Prediction.objects.create(match=self.matches[1], prediction=2, user=self.user)
        p3 = Prediction.objects.create(match=self.matches[2], prediction=3, user=self.user)

        response = self.client.post(
                reverse('competition:prediction_update', kwargs={'prediction_pk': p1.pk}),
                { 'prediction_prediction': -1,
        })

        response = self.client.get(url)
        self.assertEqual(len(response.context['predictions']), 3)
        self.assertEqual(response.context['predictions'][0].pk, p3.pk)
        self.assertEqual(response.context['predictions'][0].match.pk, 3)
        self.assertEqual(response.context['predictions'][0].prediction, 3)
        self.assertEqual(response.context['predictions'][1].pk, p2.pk)
        self.assertEqual(response.context['predictions'][1].match.pk, 2)
        self.assertEqual(response.context['predictions'][1].prediction, 2)
        self.assertEqual(response.context['predictions'][2].pk, p1.pk)
        self.assertEqual(response.context['predictions'][2].match.pk, 1)
        self.assertEqual(response.context['predictions'][2].prediction, 1)

        response = self.client.post(
                reverse('competition:prediction_update', kwargs={'prediction_pk': p3.pk}),
                { 'prediction_prediction': -1,
        })

        response = self.client.get(url)
        self.assertEqual(len(response.context['predictions']), 3)
        self.assertEqual(response.context['predictions'][0].pk, p3.pk)
        self.assertEqual(response.context['predictions'][0].match.pk, 3)
        self.assertEqual(response.context['predictions'][0].prediction, -1)
        self.assertEqual(response.context['predictions'][1].pk, p2.pk)
        self.assertEqual(response.context['predictions'][1].match.pk, 2)
        self.assertEqual(response.context['predictions'][1].prediction, 2)
        self.assertEqual(response.context['predictions'][2].pk, p1.pk)
        self.assertEqual(response.context['predictions'][2].match.pk, 1)
        self.assertEqual(response.context['predictions'][2].prediction, 1)

        response = self.client.post(
                reverse('competition:prediction_update', kwargs={'prediction_pk': 20}),
                { 'prediction_prediction': 5,
        })

        response = self.client.get(url)
        self.assertEqual(len(response.context['predictions']), 3)
        self.assertEqual(response.context['predictions'][0].pk, p3.pk)
        self.assertEqual(response.context['predictions'][0].match.pk, 3)
        self.assertEqual(response.context['predictions'][0].prediction, -1)
        self.assertEqual(response.context['predictions'][1].pk, p2.pk)
        self.assertEqual(response.context['predictions'][1].match.pk, 2)
        self.assertEqual(response.context['predictions'][1].prediction, 2)
        self.assertEqual(response.context['predictions'][2].pk, p1.pk)
        self.assertEqual(response.context['predictions'][2].match.pk, 1)
        self.assertEqual(response.context['predictions'][2].prediction, 1)

    def test_predictions_other_user(self):
        url = reverse('competition:predictions', kwargs={'slug': self.tourn.name})

        Prediction.objects.create(match=self.matches[0], prediction=1, user=self.user)
        Prediction.objects.create(match=self.matches[1], prediction=2, user=self.user)
        Prediction.objects.create(match=self.matches[2], prediction=3, user=self.user)

        response = self.client.get(url + '?user=%s' % self.other_user.username)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['predictions']), 0)

        Prediction.objects.create(match=self.matches[0], prediction=4, user=self.other_user)
        Prediction.objects.create(match=self.matches[1], prediction=-1, user=self.other_user)
        Prediction.objects.create(match=self.matches[2], prediction=-3, user=self.other_user)

        response = self.client.get(url + '?user=%s' % self.other_user.username)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['predictions']), 2)
        self.assertEqual(response.context['predictions'][0].match.pk, 2)
        self.assertEqual(response.context['predictions'][0].prediction, -1)
        self.assertEqual(response.context['predictions'][1].match.pk, 1)
        self.assertEqual(response.context['predictions'][1].prediction, 4)

        response = self.client.get(url + '?user=%s' % self.user.username)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['predictions']), 3)
        self.assertEqual(response.context['predictions'][0].match.pk, 3)
        self.assertEqual(response.context['predictions'][0].prediction, 3)
        self.assertEqual(response.context['predictions'][1].match.pk, 2)
        self.assertEqual(response.context['predictions'][1].prediction, 2)
        self.assertEqual(response.context['predictions'][2].match.pk, 1)
        self.assertEqual(response.context['predictions'][2].prediction, 1)

        response = self.client.get(url + '?user=bla')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['predictions']), 3)
        self.assertEqual(response.context['predictions'][0].match.pk, 3)
        self.assertEqual(response.context['predictions'][0].prediction, 3)
        self.assertEqual(response.context['predictions'][1].match.pk, 2)
        self.assertEqual(response.context['predictions'][1].prediction, 2)
        self.assertEqual(response.context['predictions'][2].match.pk, 1)
        self.assertEqual(response.context['predictions'][2].prediction, 1)

        response = self.client.get(url + '?bla=bla')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['predictions']), 3)
        self.assertEqual(response.context['predictions'][0].match.pk, 3)
        self.assertEqual(response.context['predictions'][0].prediction, 3)
        self.assertEqual(response.context['predictions'][1].match.pk, 2)
        self.assertEqual(response.context['predictions'][1].prediction, 2)
        self.assertEqual(response.context['predictions'][2].match.pk, 1)
        self.assertEqual(response.context['predictions'][2].prediction, 1)

    def test_results_post(self):
        url = reverse('competition:results', kwargs={'slug': self.tourn.name})

        p1 = Prediction.objects.create(match=self.matches[0], prediction=1, user=self.user)
        p2 = Prediction.objects.create(match=self.matches[1], prediction=-1, user=self.user)
        p3 = Prediction.objects.create(match=self.matches[2], prediction=3, user=self.user)
        p4 = Prediction.objects.create(match=self.matches[1], prediction=5, user=self.other_user)

        response = self.client.post(url, {
            '1': 2,
            '2': 5,
            '3': -1,
        })
        self.assertRedirects(response, reverse('account_login') + "?next=" + url)

        permission = Permission.objects.get(name='Can change match')
        self.user.user_permissions.add(permission)

        response = self.client.post(url, {
            '1': 2,
            '2': 5,
            '3': -1,
        })
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Match.objects.get(pk=1).score, 2)
        self.assertEqual(Match.objects.get(pk=2).score, 5)
        self.assertEqual(Match.objects.get(pk=3).score, None)

        for p in [p1, p2, p3, p4]:
            p.refresh_from_db()

        self.assertEqual(p1.score, -1)
        self.assertEqual(p1.margin, 1)
        self.assertEqual(p2.score, 6)
        self.assertEqual(p2.margin, 6)
        self.assertEqual(p3.score, None)
        self.assertEqual(p3.margin, None)
        self.assertEqual(p4.score, -2)
        self.assertEqual(p4.margin, 0)

        p5 = Prediction.objects.get(match_id=1, user=self.other_user)
        self.assertTrue(p5.late)
        self.assertEqual(p5.prediction, 0)
        self.assertEqual(p5.score, 2)
        self.assertEqual(p5.margin, 2)

        response = self.client.post(url, {
            '1': 3,
            '2': 3,
            '3': 3,
        })
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Match.objects.get(pk=1).score, 2)
        self.assertEqual(Match.objects.get(pk=2).score, 5)
        self.assertEqual(Match.objects.get(pk=3).score, None)


    def test_match(self):
        url = reverse('competition:match', kwargs={'match_pk': 1})

        Prediction.objects.create(match=self.matches[0], prediction=1, user=self.user)
        Prediction.objects.create(match=self.matches[1], prediction=2, user=self.user)
        Prediction.objects.create(match=self.matches[0], prediction=-1, user=self.other_user)
        Prediction.objects.create(match=self.matches[1], prediction=-1, user=self.other_user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['predictions']), 2)

        self.matches[0].score = 3
        self.matches[0].save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['predictions']), 2)

        self.tourn.test_features_enabled = True
        self.tourn.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['predictions']), 2)

        response = self.client.get(url + "?benchmarks=show")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['predictions']), 3)

    def test_prediction_create(self):
        response = self.client.post(
                reverse('competition:prediction_create', kwargs={'match_pk': 1}),
                { 'prediction_prediction': -1})
        self.assertEqual(response.status_code, 404)

        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 0)

        response = self.client.post(
                reverse('competition:prediction_create', kwargs={'match_pk': 2}),
                { 'prediction_prediction': 2})
        self.assertEqual(response.status_code, 404)

        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 0)

        response = self.client.post(
                reverse('competition:prediction_create', kwargs={'match_pk': 3}),
                { 'prediction_prediction': -3})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/messages.html')

        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 1)
        self.assertEqual(Prediction.objects.get(match__pk=3, user=self.user).prediction, -3)

        response = self.client.post(
                reverse('competition:prediction_create', kwargs={'match_pk': 4}),
                { 'prediction_prediction': 'home'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/prediction_create.html')
        self.assertEqual(response.context['error'], True)
        self.assertFalse('prediction' in response.context)
        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 1)
        predictions = Prediction.objects.filter(match__pk=4, user=self.user)
        self.assertEqual(len(predictions), 0)

        response = self.client.post(
                reverse('competition:prediction_create', kwargs={'match_pk': 6}),
                { 'prediction_prediction': 5})
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
                reverse('competition:prediction_create', kwargs={'match_pk': 3}),
                { 'prediction_prediction': 3}) # create again
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/messages.html')

        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 1)
        self.assertEqual(Prediction.objects.get(match__pk=3, user=self.user).prediction, -3)

        # posts from match_view
        response = self.client.post(
                reverse('competition:prediction_create', kwargs={'match_pk': 4}) + '?match_view=true',
                { 'prediction_prediction': 4})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/match_prediction_form.html')

        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 2)
        prediction = Prediction.objects.get(match__pk=4, user=self.user)
        self.assertEqual(prediction.prediction, 4)
        self.assertEqual(prediction, response.context['prediction'])

    def test_prediction_update(self):
        p1 = Prediction.objects.create(match=self.matches[0], prediction=1, user=self.user)
        p2 = Prediction.objects.create(match=self.matches[1], prediction=-1, user=self.user)
        p3 = Prediction.objects.create(match=self.matches[2], prediction=3, user=self.user)
        p4 = Prediction.objects.create(match=self.matches[1], prediction=5, user=self.other_user)

        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 3)

        response = self.client.post(
                reverse('competition:prediction_update', kwargs={'prediction_pk': p1.pk}),
                { 'prediction_prediction': -1,
        })
        self.assertEqual(response.status_code, 404)
        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 3)
        self.assertEqual(Prediction.objects.get(pk=p1.pk, user=self.user).prediction, 1)

        response = self.client.post(
                reverse('competition:prediction_update', kwargs={'prediction_pk': p3.pk}),
                { 'prediction_prediction': -1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/prediction_update.html')
        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 3)
        self.assertEqual(Prediction.objects.get(pk=p3.pk, user=self.user).prediction, -1)

        response = self.client.post(
                reverse('competition:prediction_update', kwargs={'prediction_pk': 20}),
                { 'prediction_prediction': 5,
        })
        self.assertEqual(response.status_code, 404)
        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 3)

        response = self.client.post(
                reverse('competition:prediction_update', kwargs={'prediction_pk': p3.pk}),
                { 'prediction_prediction': 'home',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/prediction_update.html')
        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 3)
        self.assertEqual(Prediction.objects.get(pk=p3.pk, user=self.user).prediction, -1)

        response = self.client.post(
                reverse('competition:prediction_update', kwargs={'prediction_pk': p4.pk}),
                { 'prediction_prediction': 5,
        })
        self.assertEqual(response.status_code, 404)

        # match_view post
        response = self.client.post(
                reverse('competition:prediction_update', kwargs={'prediction_pk': p2.pk}) + '?match_view=true',
                { 'prediction_prediction': 5,
        })
        self.assertEqual(response.status_code, 404)
        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 3)

        response = self.client.post(
                reverse('competition:prediction_update', kwargs={'prediction_pk': p3.pk}) + '?match_view=true',
                { 'prediction_prediction': 5,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partial/match_prediction_form.html')
        predictions = Prediction.objects.filter(user=self.user)
        self.assertEqual(len(predictions), 3)
        self.assertEqual(Prediction.objects.get(pk=p3.pk, user=self.user).prediction, 5)


def pre_save_for_prediction_fixture(sender, instance, **kwargs):
    if kwargs['raw']:
        instance.entered = timezone.now()
pre_save.connect(pre_save_for_prediction_fixture, sender=Prediction)


class BenchmarkAlgorithms(TestCase):
    fixtures = [
            'social.json',
            'accounts.json',
            'teams.json',
            'predictions.json'
            ]

    @classmethod
    def setUpTestData(cls):
        cls.tourn = Tournament.objects.get(name='active_tourn')

    def test_mean(self):
        bm = Benchmark.objects.create(tournament=self.tourn, name="mean", prediction_algorithm=Benchmark.MEAN)

        expected_results = [
                # (match.pk, result),
                (1, 0),
                # (2, Decimal(0.6)),   '0.599999999999999977795'
                (3, 1.25),
                (4, 0),
                ]

        for pk, expected in expected_results:
            match = Match.objects.get(pk=pk)

            p = bm.predict(match)
            self.assertEqual(p.prediction, expected)

    def test_median(self):
        bm = Benchmark.objects.create(tournament=self.tourn, name="median", prediction_algorithm=Benchmark.MEDIAN)

        expected_results = [
                # (match.pk, result),
                (1, 0),
                (2, 1),
                (3, 1.5),
                (4, 1.5),
                ]

        for pk, expected in expected_results:
            match = Match.objects.get(pk=pk)

            p = bm.predict(match)
            self.assertEqual(p.prediction, expected)


class CsvTeamUploadTest(TestCase):
    fixtures = ['accounts.json']

    def setUp(self):
        # staff and superuser
        self.user = User.objects.get(username='testuser1')
        self.client.force_login(self.user)

    def test_team_upload(self):
        add_url = reverse('admin:competition_sport_add')
        list_url = reverse('admin:competition_sport_changelist')
        with open('test/teams_A_to_H_upload.csv') as fd:
            response = self.client.post(add_url, {
                'name': 'sport',
                'scoring_unit': 'point',
                'match_start_verb': 'Kick Off',
                'add_teams': fd,
                'team_set-TOTAL_FORMS': 0,
                'team_set-INITIAL_FORMS': 0,
                '_save': 'Save',
            })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, list_url)

        s = Sport.objects.get(name='sport')

        self.assertEqual(s.name, 'sport')

        teams = s.team_set.all()
        self.assertEqual(len(teams), 8)

        # get set of expected teams from first 8 letters
        expected = set([(f'Team {l}', f'{l*3}') for l in string.ascii_uppercase[:8]])
        self.assertEqual(set(teams.values_list('name', 'code')), expected)

        edit_url = reverse('admin:competition_sport_change', args=[s.pk])

        with open('test/teams_E_to_J_upload.csv') as fd:
            response = self.client.post(edit_url, {
                'name': 'sport',
                'scoring_unit': 'point',
                'match_start_verb': 'Kick Off',
                'add_teams': fd,
                'team_set-TOTAL_FORMS': 0,
                'team_set-INITIAL_FORMS': 0,
                '_save': 'Save',
            })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, list_url)

        s = Sport.objects.get(name='sport')

        self.assertEqual(s.name, 'sport')

        teams = s.team_set.all()
        self.assertEqual(len(teams), 10)

        # get set of expected teams from first 8 letters
        expected = set([(f'Team {l}', f'{l*3}') for l in string.ascii_uppercase[:10]])
        self.assertEqual(set(teams.values_list('name', 'code')), expected)


class CsvMatchUploadTest(TestCase):
    fixtures = [
            'accounts.json',
            'teams.json',
            ]

    def setUp(self):
        # staff and superuser
        self.user = User.objects.get(username='testuser1')
        self.client.force_login(self.user)

    def test_match_upload(self):
        add_url = reverse('admin:competition_tournament_add')
        list_url = reverse('admin:competition_tournament_changelist')
        with open('test/matches_upload.csv') as fd:
            response = self.client.post(add_url, {
                'name': 'new tourn',
                'slug': 'new-tourn',
                'sport': "1",
                'state': 0,
                'bonus': 2,
                'draw_bonus': 1,
                'year': 2022,
                'add_matches': fd,
                '_save': 'Save',
            })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, list_url)

        t = Tournament.objects.get(name='new tourn')

        self.assertEqual(t.name, 'new tourn')

        matches = t.match_set.all()
        # Team E does not exist
        self.assertEqual(len(matches), 3)
        self.assertEqual(f"{matches[0]}", "Team A Vs Team B")
        self.assertEqual(f"{matches[1]}", "Team C Vs Team D")
        self.assertEqual(f"{matches[2]}", "Team G Vs Team H")

        Team.objects.create(name="Team E", code="EEE", sport=t.sport)

        edit_url = reverse('admin:competition_tournament_change', args=[t.pk])

        with open('test/matches_upload_winner_of.csv') as fd:
            response = self.client.post(edit_url, {
                'name': 'new tourn',
                'slug': 'new-tourn',
                'add_matches': fd,
                '_save': 'Save',
                'benchmark_set-TOTAL_FORMS': 0,
                'benchmark_set-INITIAL_FORMS': 0,
                'participant_set-TOTAL_FORMS': 0,
                'participant_set-INITIAL_FORMS': 0,
            })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, list_url)

        matches = t.match_set.all()
        self.assertEqual(len(matches), 9)

        self.assertEqual(f"{matches[0]}", "Team A Vs Team B")
        self.assertEqual(f"{matches[1]}", "Team C Vs Team D")
        self.assertEqual(f"{matches[2]}", "Team G Vs Team H")
        self.assertEqual(f"{matches[3]}", "Team E Vs Team F")
        self.assertEqual(f"{matches[4]}", "Team A/Team B Vs Team C/Team D")
        self.assertEqual(f"{matches[5]}", "Team E/Team F Vs Team I")
        self.assertEqual(f"{matches[6]}", "Team J Vs Team G/Team H")
        self.assertEqual(f"{matches[7]}", "Team E/Team F/Team I Vs Team J/Team G/Team H")
        self.assertEqual(f"{matches[8]}", "Team A/Team B/Team C/Team D Vs Team E/Team F/Team I/Team J/Team G/Team H")
