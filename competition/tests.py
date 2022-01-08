from django.contrib.auth.models import User, Permission
from django.test import TestCase, TransactionTestCase
from django.core.urlresolvers import reverse
from django.utils import timezone

import datetime
import pytz
import unittest

from .models import Sport, Tournament, Participant
from .models import Benchmark, Team, Match, Prediction

class CompetitionViewLoggedOutTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url_login_next = reverse('account_login') + "?next="

    def test_index(self):
        url = reverse('competition:index')
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_predictions(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_table(self):
        url = reverse('competition:table', kwargs={'tour_name':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_org_table(self):
        url = reverse('competition:org_table', kwargs={'tour_name':'tourn', 'org_name': 'org'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_join(self):
        url = reverse('competition:join', kwargs={'tour_name':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_results(self):
        url = reverse('competition:results', kwargs={'tour_name':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_rules(self):
        url = reverse('competition:rules', kwargs={'tour_name':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_match(self):
        url = reverse('competition:match', kwargs={'match_pk':1})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_benchmark_table(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

    def test_benchmark(self):
        url = reverse('competition:benchmark', kwargs={'benchmark_pk': 1})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)


class CompetitionViewNotParticipantTest(TestCase):
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
        url = reverse('competition:submit', kwargs={'tour_name':'pending_tourn'})
        join_url = reverse('competition:join', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, join_url)

    def test_submit_active(self):
        url = reverse('competition:submit', kwargs={'tour_name':'active_tourn'})
        join_url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, join_url)

    def test_submit_finished(self):
        url = reverse('competition:submit', kwargs={'tour_name':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_submit_archived(self):
        url = reverse('competition:submit', kwargs={'tour_name':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_predictions_pending(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'pending_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, r_url)

    def test_predictions_active(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'active_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, r_url)

    def test_predictions_finished(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_predictions_archived(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_table_pending(self):
        url = reverse('competition:table', kwargs={'tour_name':'pending_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_table_active(self):
        url = reverse('competition:table', kwargs={'tour_name':'active_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_table_finished(self):
        url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_table_archived(self):
        url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_join_pending(self):
        url = reverse('competition:join', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join.html')

        count_before = len(Participant.objects.filter(tournament__name='pending_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='pending_tourn'))
        self.assertEqual(count_after, count_before + 1)

        r_url = reverse('competition:submit', kwargs={'tour_name':'pending_tourn'})
        self.assertRedirects(response, r_url)

    def test_join_active(self):
        url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join.html')

        count_before = len(Participant.objects.filter(tournament__name='active_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='active_tourn'))
        self.assertEqual(count_after, count_before + 1)

        r_url = reverse('competition:submit', kwargs={'tour_name':'active_tourn'})
        self.assertRedirects(response, r_url)

    def test_join_finished(self):
        url = reverse('competition:join', kwargs={'tour_name':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)
        count_before = len(Participant.objects.filter(tournament__name='finished_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='finished_tourn'))
        self.assertEqual(count_after, count_before)

        self.assertRedirects(response, r_url)

    def test_join_archived(self):
        url = reverse('competition:join', kwargs={'tour_name':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

        count_before = len(Participant.objects.filter(tournament__name='archived_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='archived_tourn'))
        self.assertEqual(count_after, count_before)

        self.assertRedirects(response, r_url)

    def test_results_pending(self):
        url = reverse('competition:results', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_active(self):
        url = reverse('competition:results', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_finished(self):
        url = reverse('competition:results', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_archived(self):
        url = reverse('competition:results', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_rules_pending(self):
        url = reverse('competition:rules', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_rules_active(self):
        url = reverse('competition:rules', kwargs={'tour_name':'active_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_rules_finished(self):
        url = reverse('competition:rules', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_rules_archived(self):
        url = reverse('competition:rules', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

#     def test_match_pending(self):
#     def test_match_active(self):
#     def test_match_finished(self):
#     def test_match_archived(self):
# 
    def test_benchmark_table_pending(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'pending_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_benchmark_table_active(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'active_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_benchmark_table_finished(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, r_url)

    def test_benchmark_table_archived(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, r_url)


class CompetitionViewTest(TestCase):

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
        url = reverse('competition:submit', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'submit.html')

    def test_submit_active(self):
        url = reverse('competition:submit', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'submit.html')

    def test_submit_finished(self):
        url = reverse('competition:submit', kwargs={'tour_name':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_submit_archived(self):
        url = reverse('competition:submit', kwargs={'tour_name':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_predictions_pending(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_predictions_active(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_predictions_finished(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_predictions_archived(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_table_pending(self):
        url = reverse('competition:table', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_table_active(self):
        url = reverse('competition:table', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_table_finished(self):
        url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_table_archived(self):
        url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    @unittest.skip("transaction error")
    def test_join_pending(self):
        url = reverse('competition:join', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join.html')

        count_before = len(Participant.objects.filter(tournament__name='pending_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='pending_tourn'))
        self.assertEqual(count_after, count_before)

        r_url = reverse('competition:submit', kwargs={'tour_name':'pending_tourn'})
        self.assertRedirects(response, r_url)

    @unittest.skip("transaction error")
    def test_join_active(self):
        url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join.html')

        count_before = len(Participant.objects.filter(tournament__name='active_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='active_tourn'))
        self.assertEqual(count_after, count_before)

        r_url = reverse('competition:submit', kwargs={'tour_name':'active_tourn'})
        self.assertRedirects(response, r_url)

    def test_join_finished(self):
        url = reverse('competition:join', kwargs={'tour_name':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)
        count_before = len(Participant.objects.filter(tournament__name='finished_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='finished_tourn'))
        self.assertEqual(count_after, count_before)

        self.assertRedirects(response, r_url)

    def test_join_archived(self):
        url = reverse('competition:join', kwargs={'tour_name':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

        count_before = len(Participant.objects.filter(tournament__name='archived_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='archived_tourn'))
        self.assertEqual(count_after, count_before)

        self.assertRedirects(response, r_url)

    def test_results_pending(self):
        url = reverse('competition:results', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_active(self):
        url = reverse('competition:results', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_finished(self):
        url = reverse('competition:results', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_archived(self):
        url = reverse('competition:results', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, self.url_login_next + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_rules_pending(self):
        url = reverse('competition:rules', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_rules_active(self):
        url = reverse('competition:rules', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_rules_finished(self):
        url = reverse('competition:rules', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_rules_archived(self):
        url = reverse('competition:rules', kwargs={'tour_name':'archived_tourn'})
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
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_benchmark_table_active(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_benchmark_table_finished(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_benchmark_table_archived(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'archived_tourn'})
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

    def test_submit_post(self):
        url = reverse('competition:submit', kwargs={'tour_name':self.tourn.name})
        response = self.client.post(url, {
            '1': -1,
            '2': 2,
            '3': -3,
            '4': "home",
            '6': -5,
        })

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

        response = self.client.post(url, {
            '3': 3,
            '4': 4,
        })

        self.assertEqual(len(response.context['fixture_list']), 1)

        predictions = Prediction.objects.filter(match__pk=3, user=self.user)
        self.assertEqual(len(predictions), 1)
        self.assertEqual(predictions[0].prediction, -3)
        self.assertFalse(predictions[0].late)
        predictions = Prediction.objects.filter(match__pk=4, user=self.user)
        self.assertEqual(len(predictions), 1)
        self.assertEqual(predictions[0].prediction, 4)

    def test_predictions_post(self):
        url = reverse('competition:predictions', kwargs={'tour_name': self.tourn.name})

        p1 = Prediction.objects.create(match=self.matches[0], prediction=1, user=self.user)
        p2 = Prediction.objects.create(match=self.matches[1], prediction=2, user=self.user)
        p3 = Prediction.objects.create(match=self.matches[2], prediction=3, user=self.user)

        response = self.client.post(url, {
            'prediction_id': p1.pk,
            'prediction_prediction': -1,
        })

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

        response = self.client.post(url, {
            'prediction_id': p3.pk,
            'prediction_prediction': -1,
        })

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

        response = self.client.post(url, {
            'prediction_id': 20,
            'prediction_prediction': 5,
        })

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
        url = reverse('competition:predictions', kwargs={'tour_name': self.tourn.name})

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
        url = reverse('competition:results', kwargs={'tour_name': self.tourn.name})

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
