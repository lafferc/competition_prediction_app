from django.db import models, IntegrityError, transaction
from django.db.models import Avg, Max
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core import mail
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils import timezone
from io import StringIO
import logging
import csv
import datetime
import random
from decimal import Decimal
import statistics

g_logger = logging.getLogger(__name__)


def current_year():
    return datetime.datetime.today().year


YEAR_CHOICES = [(r, r) for r in range(2016, current_year() + 2)]


class Sport(models.Model):
    name = models.CharField(max_length=50, unique=True)
    scoring_unit = models.CharField(max_length=50, default="point")
    match_start_verb = models.CharField(max_length=50, default="Kick Off")
    add_teams = models.FileField(null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        csv_file = self.add_teams
        self.add_teams = None
        super(Sport, self).save(*args, **kwargs)

        if csv_file:
            self.handle_teams_upload(csv_file)

    def handle_teams_upload(self, csv_file):

        io_file = csv_file.read().decode('utf-8')

        g_logger.info("handle_teams_upload for %s csv:%s" % (self, csv_file))
        reader = csv.DictReader(StringIO(io_file), delimiter=',')
        for row in reader:
            try:
                row['sport'] = self
                with transaction.atomic():
                    Team(**row).save()
            except IntegrityError as e:
                g_logger.error(f"Failed to add team({row['name']}, {row['code']}) -- {e}")


class Team(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=3)
    sport = models.ForeignKey(Sport, models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('code', 'sport',)
        unique_together = ('name', 'sport',)


class Tournament(models.Model):
    PENDING = 0
    ACTIVE = 1
    FINISHED = 2
    ARCHIVED = 3

    name = models.CharField(max_length=200, unique=True)
    participants = models.ManyToManyField(User, through="Participant")
    sport = models.ForeignKey(Sport, models.CASCADE)
    bonus = models.DecimalField(max_digits=5, decimal_places=2, default=2)
    draw_bonus = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    state = models.IntegerField(default=PENDING,
                                choices=((PENDING, "Pending"),
                                         (ACTIVE, "Active"),
                                         (FINISHED, "Finished"),
                                         (ARCHIVED, "Archived")))
    winner = models.ForeignKey("Participant",
                               models.CASCADE,
                               null=True,
                               blank=True,
                               related_name='+')
    add_matches = models.FileField(null=True, blank=True)
    year = models.IntegerField(choices=YEAR_CHOICES, default=current_year)
    test_features_enabled = models.BooleanField(default=False)
    draw_definition = models.CharField(
            max_length=20,
            default="extra_time",
            choices=(("normal_time", "normal_time"),
                     ("extra_time", "extra_time"),),
            null=True,
            blank=True)
    slug = models.SlugField(unique=True)
    additional_rules = models.TextField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse('competition:submit', kwargs={'slug': self.slug})

    def is_closed(self):
        return self.state in [self.FINISHED, self.ARCHIVED]

    def __str__(self):
        return self.name

    def update_table(self):
        g_logger.debug("%s update_table" % self)
        for participant in self.participant_set.all():
            participant.update_score()

        for benchmark in self.benchmark_set.all():
            benchmark.update_score()

    def check_predictions(self, match):
        g_logger.debug("%s: update_scores for %s", self, match)

        for participant in self.participant_set.all():
            participant.check_prediction(match)

        for benchmark in self.benchmark_set.all():
            benchmark.check_prediction(match)

        self.update_table()

    def find_team(self, name):
        try:
            return Team.objects.get(sport=self.sport, name=name)
        except Team.DoesNotExist:
            return Team.objects.get(sport=self.sport, code=name)

    def close(self, request):
        if self.state != Tournament.ACTIVE:
            return
        self.update_table()
        self.winner = Participant.objects.filter(tournament=self).order_by("score")[0]
        self.state = Tournament.FINISHED

        current_site = get_current_site(request)
        subject = "Thank you for participating in %s" % self.name

        n_sent = 0
        connection = mail.get_connection()
        connection.open()
        for user in self.participants.all():
            message = render_to_string('close_email.html', {
                'user': user,
                'winner': self.winner.user.profile.get_name(),
                'winner_score': "%.2f" % self.winner.score,
                'tournament_name': self.name,
                'site_name': current_site.name,
            })
            if user.profile.email_user(subject,
                                       message,
                                       connection=connection):
                n_sent += 1

        connection.close()
        messages.success(request,
                         'The tournament "%s" was closed successfully, %d emails sent.' % (self.name, n_sent))

        self.save()

    def open(self, request):
        if self.state != Tournament.PENDING:
            g_logger.error("can only open tournaments that are pending")
            return
        self.state = Tournament.ACTIVE

        current_site = get_current_site(request)
        subject = "A new competition has started"

        n_sent = 0
        connection = mail.get_connection()
        connection.open()
        for user in User.objects.all():
            message = render_to_string('open_email.html', {
                'user': user,
                'tournament': self,
                'site_name': current_site.name,
                'site_domain': current_site.name,
                'protocol': 'https' if request.is_secure() else 'http',
            })
            if user.profile.email_user(subject,
                                       message,
                                       new_comp=True,
                                       connection=connection):
                n_sent += 1

        connection.close()
        messages.success(request,
                         'The tournament "%s" was opened successfully, %d emails sent.' % (self.name, n_sent))

        self.save()

    def save(self, *args, **kwargs):
        csv_file = self.add_matches
        self.add_matches = None

        if not self.slug:
            self.slug = slugify(self.name)

        super(Tournament, self).save(*args, **kwargs)

        if csv_file:
            self.handle_match_upload(csv_file)

    def handle_match_upload(self, csv_file):
        io_file = csv_file.read().decode('utf-8')

        g_logger.info("handle_match_upload for %s csv:%s"
                      % (self, csv_file))
        reader = csv.DictReader(StringIO(io_file), delimiter=',')
        for row in reader:
            g_logger.debug("Row: %r" % row)
            if not row:
                continue
            try:
                row['tournament'] = self
                if row['home_team'] == "TBD":
                    row['home_team'] = None
                    row['home_team_winner_of'] = self.match_set.get(
                        match_id=row['home_team_winner_of'])
                else:
                    row['home_team'] = self.find_team(row['home_team'])
                    row['home_team_winner_of'] = None
                if row['away_team'] == "TBD":
                    row['away_team'] = None
                    row['away_team_winner_of'] = self.match_set.get(
                        match_id=row['away_team_winner_of'])
                else:
                    row['away_team'] = self.find_team(row['away_team'])
                    row['away_team_winner_of'] = None
                with transaction.atomic():
                    Match(**row).save()
            except (IntegrityError, ValidationError, Team.DoesNotExist, Match.DoesNotExist) as e:
                g_logger.error(f"Failed to add match {row} -- {e}")

    class Meta:
        permissions = (
            ("csv_upload", "Can add matches via CSV upload file"),
        )


class Predictor(models.Model):
    tournament = models.ForeignKey(Tournament, models.CASCADE)
    score = models.DecimalField(blank=True, null=True, max_digits=6, decimal_places=2)
    margin_per_match = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2)

    def save(self, *args, **kwargs):
        created = False
        if self._state.adding:
            g_logger.debug("New Predictor %s added (pre-save)" % self)
            created = True

        super(Predictor, self).save(*args, **kwargs)

        if created:
            g_logger.debug("%s: Calculating prediction for each existing match", self)
            for match in Match.objects.filter(tournament=self.tournament,
                                              kick_off__lt=timezone.now(),
                                              postponed=False):
                prediction = self.predict(match)

                if match.score is not None:
                    prediction.calc_score(match.score)
                prediction.save()
            self.tournament.update_table()

    def get_name(self):
        raise NotImplementedError("%s didn't override get_name" % self.__class__)

    def predict(self, match):
        raise NotImplementedError("%s didn't override predict" % self.__class__)

    def get_predictions(self):
        raise NotImplementedError("%s didn't override get_predictions" % self.__class__)

    def get_or_create_prediction(self, match):
        raise NotImplementedError("%s didn't override get_or_create_prediction" % self.__class__)

    def get_url(self):
        return None

    def check_prediction(self, match):
        prediction = self.get_or_create_prediction(match)
        prediction.calc_score(match.score)
        prediction.save()

    def update_score(self):
        score = 0
        total_margin = 0
        num_predictions = 0
        for prediction in self.get_predictions():
            if prediction.score is not None:
                score += prediction.score
            if prediction.margin is not None:
                total_margin += prediction.margin
                num_predictions += 1
        if num_predictions == 0:
            return
        self.score = score
        self.margin_per_match = (total_margin / num_predictions)
        self.save()

    class Meta:
        abstract = True


class Participant(Predictor):
    user = models.ForeignKey(User, models.CASCADE)

    def __str__(self):
        return "%s:%s" % (self.tournament, self.user)

    def get_name(self):
        return self.user.profile.get_name()

    def predict(self, match):
        return Prediction(user=self.user, match=match, late=True)

    def get_predictions(self):
        return Prediction.objects.filter(user=self.user).filter(match__tournament=self.tournament)

    def get_or_create_prediction(self, match):
        try:
            return Prediction.objects.get(user=self.user, match=match)
        except Prediction.DoesNotExist:
            g_logger.debug("%s did not predict %s" % (self.user, match))
            return self.predict(match)

    def get_url(self):
        return "%s?user=%s" % (
            reverse('competition:predictions', args=(self.tournament.slug,)),
            self.user.username)

    class Meta:
        unique_together = ('tournament', 'user',)


class Match(models.Model):
    tournament = models.ForeignKey(Tournament, models.CASCADE)
    match_id = models.IntegerField(blank=True)
    kick_off = models.DateTimeField(verbose_name='Start Time')
    home_team = models.ForeignKey(Team,
                                  models.CASCADE,
                                  related_name='match_home_team',
                                  null=True,
                                  blank=True)
    home_team_winner_of = models.ForeignKey('self',
                                            models.CASCADE,
                                            blank=True,
                                            null=True,
                                            related_name='match_next_home')
    away_team = models.ForeignKey(Team,
                                  models.CASCADE,
                                  related_name='match_away_team',
                                  null=True,
                                  blank=True)
    away_team_winner_of = models.ForeignKey('self',
                                            models.CASCADE,
                                            blank=True,
                                            null=True,
                                            related_name='match_next_away')
    score = models.IntegerField(blank=True, null=True)
    postponed = models.BooleanField(blank=True, default=False)

    def __str__(self):
        s = ''
        if not self.home_team:
            s += self.home_team_winner_of.to_be_decided_str()
        else:
            s += self.home_team.name
        s += " Vs "
        if not self.away_team:
            s += self.away_team_winner_of.to_be_decided_str()
        else:
            s += self.away_team.name
        return s

    def to_be_decided_str(self):
        s = ''
        if not self.home_team:
            s += self.home_team_winner_of.to_be_decided_str()
        else:
            s += self.home_team.name
        s += "/"
        if not self.away_team:
            s += self.away_team_winner_of.to_be_decided_str()
        else:
            s += self.away_team.name
        return s

    def check_next_round_matches(self):
        if not self.score:
            return  # no winner
        if self.score > 0:
            winner = self.home_team
        else:
            winner = self.away_team

        for next_round in self.match_next_home.all():
            next_round.home_team = winner
            next_round.home_team_winner_of = None
            next_round.save()

        for next_round in self.match_next_away.all():
            next_round.away_team = winner
            next_round.away_team_winner_of = None
            next_round.save()

    def has_started(self):
        if self.postponed:
            return False
        if self.kick_off > timezone.now():
            return False
        return True

    def save(self, *args, **kwargs):
        created = False
        if self._state.adding:
            g_logger.debug("New Match added (pre-save) %s" % self)
            created = True

            if self.match_id is None:
                g_logger.debug("New Match %s doesn't has a match_id", self)
                query = Match.objects.filter(tournament=self.tournament)
                curr_max_id = query.aggregate(Max('match_id'))['match_id__max']
                g_logger.debug("Max value of used match_id is %s", curr_max_id)
                self.match_id = curr_max_id + 1 if curr_max_id else 1

        super(Match, self).save(*args, **kwargs)

        if not created and self.score is not None:
            self.tournament.check_predictions(self)
            g_logger.debug("checking for next round matches: %s", self)
            self.check_next_round_matches()

    class Meta:
        unique_together = ('tournament', 'match_id',)
        verbose_name_plural = "matches"


class PredictionBase(models.Model):
    match = models.ForeignKey(Match, models.CASCADE)
    prediction = models.DecimalField(default=0, max_digits=5, decimal_places=2)
    score = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2)
    margin = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2)
    correct = models.NullBooleanField()

    def calc_score(self, result):
        self.margin = abs(result - self.prediction)
        if self.prediction == result:
            self.score = -self.bonus(result)
            self.correct = True
        elif (self.prediction < 0 and result < 0) or (self.prediction > 0 and result > 0):
            self.score = self.margin - self.bonus(result)
            self.correct = True
        else:
            self.score = self.margin
            self.correct = False

    def bonus(self, result):
        if result == 0:  # draw
            return self.match.tournament.bonus * self.match.tournament.draw_bonus
        return self.match.tournament.bonus

    def get_predictor(self):
        raise NotImplementedError("%s didn't override get_predictor" % self.__class__)

    def css_class_correct(self):
        if self.correct is True:
            return "prediction_correct"
        if self.correct is False:
            return "prediction_incorrect"
        return "prediction_unknown"

    class Meta:
        abstract = True


class Prediction(PredictionBase):
    entered = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, models.CASCADE)
    late = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return "%s: %s" % (self.user, self.match)

    def bonus(self, result):
        if self.late:
            return 0
        return super(Prediction, self).bonus(result)

    def get_predictor(self):
        return self.match.tournament.participant_set.get(user=self.user)

    def css_class_correct(self):
        if self.late:
            return "prediction_missed"
        return super(Prediction, self).css_class_correct()

    class Meta:
        unique_together = ('user', 'match',)
        ordering = ['-match__kick_off', '-match__match_id']


class Benchmark(Predictor):
    STATIC = 0
    MEAN = 1
    RANDOM = 2
    MEDIAN = 3

    name = models.CharField(max_length=50)
    prediction_algorithm = models.IntegerField(choices=(
        (STATIC, "Fixed value"),
        (MEAN, "Average (mean)"),
        (MEDIAN, "Median"),
        (RANDOM, "Random range")))
    static_value = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2)
    range_start = models.IntegerField(blank=True, null=True)
    range_end = models.IntegerField(blank=True, null=True)

    def __str__(self):
        if self.prediction_algorithm == self.STATIC:
            return "%s STATIC(%d) %s" % (self.tournament, self.static_value, self.name)
        elif self.prediction_algorithm == self.MEAN:
            return "%s MEAN %s" % (self.tournament, self.name)
        elif self.prediction_algorithm == self.MEDIAN:
            return "%s MEDIAN %s" % (self.tournament, self.name)
        elif self.prediction_algorithm == self.RANDOM:
            return "%s RANDOM(%d, %d) %s" % (self.tournament, self.range_start,
                                             self.range_end, self.name)
        return "%s OTHER %s" % (self.tournament, self.name)

    def clean(self):
        super(Benchmark, self).clean()

        if self.prediction_algorithm == self.STATIC:
            self.clean_static()
        elif self.prediction_algorithm in [self.MEAN, self.MEDIAN]:
            self.clean_mean()
        elif self.prediction_algorithm == self.RANDOM:
            self.clean_random()

    def clean_static(self):
        if self.static_value is None:
            raise ValidationError('Static value is required for this prediction algorithm')
        if self.range_start is not None or self.range_end is not None:
            raise ValidationError('Range is not used with this prediction algorithm')

    def clean_mean(self):
        if self.static_value is not None:
            raise ValidationError('Static value is not used with this prediction algorithm')
        if self.range_start is not None or self.range_end is not None:
            raise ValidationError('Range is not used with this prediction algorithm')

    def clean_random(self):
        if self.static_value is not None:
            raise ValidationError('Static value is not used with this prediction algorithm')
        if self.range_start is None:
            raise ValidationError('Range start is required for this prediction algorithm')
        if self.range_end is None:
            raise ValidationError('Range end is required for this prediction algorithm')
        if self.range_start > self.range_end:
            raise ValidationError('Range start must be less than range end')

    def get_name(self):
        return self.name

    def predict(self, match):
        prediction = BenchmarkPrediction(benchmark=self, match=match)

        if self.prediction_algorithm == self.STATIC:
            prediction.prediction = self.static_value
        elif self.prediction_algorithm == self.MEAN:
            result = Prediction.objects.filter(match=match, late=False).aggregate(Avg('prediction'))
            if result['prediction__avg'] is not None:
                prediction.prediction = Decimal(result['prediction__avg'])
                if abs(prediction.prediction) < 0.5:
                    prediction.prediction = 0
            else:
                prediction.prediction = 0
        elif self.prediction_algorithm == self.RANDOM:
            prediction.prediction = random.randint(self.range_start, self.range_end)
        elif self.prediction_algorithm == self.MEDIAN:
            results = Prediction.objects.filter(match=match, late=False).values_list('prediction', flat=True)
            median = statistics.median(results)
            prediction.prediction = median

        return prediction

    def get_predictions(self):
        return self.benchmarkprediction_set.all()

    def get_or_create_prediction(self, match):
        try:
            return BenchmarkPrediction.objects.get(benchmark=self, match=match)
        except BenchmarkPrediction.DoesNotExist:
            g_logger.debug("%s did not predict %s" % (self, match))
            return self.predict(match)

    def get_url(self):
        return reverse('competition:benchmark', args=(self.pk,))


class BenchmarkPrediction(PredictionBase):
    benchmark = models.ForeignKey(Benchmark, models.CASCADE)

    def __str__(self):
        return "%s: %s" % (self.benchmark, self.match)

    def get_predictor(self):
        return self.benchmark

    class Meta:
        unique_together = ('benchmark', 'match',)
        ordering = ['-match__kick_off', '-match__match_id']

