from django.shortcuts import redirect, get_object_or_404, render
from django.http import HttpResponse, Http404
from django.template import loader
from django.template.defaultfilters import pluralize
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

import logging
import decimal
import datetime
from itertools import chain
from .models import Tournament, Match, Prediction, Participant, Benchmark
from member.models import Competition

g_logger = logging.getLogger(__name__)


@login_required
def index(request):
    template = loader.get_template('index.html')
    current_site = get_current_site(request)
    context = {
        'site_name': current_site.name,
        'all_tournaments': Tournament.objects.all(),
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
    }
    return HttpResponse(template.render(context, request))


@login_required
def submit(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)

    if tournament.is_closed():
        return redirect("competition:table", slug=slug)

    if not tournament.participants.filter(pk=request.user.pk).exists():
        return redirect("competition:join", slug=slug)

    fixture_list = Match.objects.filter(
        Q(postponed=True) | Q(kick_off__gt=timezone.now()),
        tournament=tournament).order_by('kick_off')

    predicted_matches = [p.match.pk for p in Prediction.objects.filter(user=request.user,
                                                                       match__tournament=tournament)]

    fixture_list = fixture_list.exclude(pk__in=predicted_matches)

    paginator = Paginator(fixture_list, 10, orphans=3)
    page = request.GET.get('page')
    fixture_list = paginator.get_page(page)

    current_site = get_current_site(request)
    template = loader.get_template('submit.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT': tournament,
        'fixture_list': fixture_list,
        'is_participant': True,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
    }
    return HttpResponse(template.render(context, request))


@login_required
def predictions(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)

    is_participant = True
    if not tournament.participants.filter(pk=request.user.pk).exists():
        if not tournament.is_closed():
            return redirect("competition:table", slug=slug)
        is_participant = False

    other_user = None
    user_score = None

    if request.GET:
        try:
            other_user = User.objects.get(username=request.GET['user'])
            if other_user == request.user:
                other_user = None
            else:
                predictions = Prediction.objects.filter(user=other_user,
                                                        match__tournament=tournament,
                                                        match__kick_off__lt=timezone.now(),
                                                        match__postponed=False
                                                        ).order_by('-match__kick_off')
                other_user = other_user.profile.get_name()
        except User.DoesNotExist:
            g_logger.debug("User(%s) tried to look at %s's predictions but '%s' does not exist"
                  % (request.user, request.GET['user'], request.GET['user']))
        except KeyError:
            other_user = None

    if not other_user:
        if not is_participant:
            return redirect("competition:table", slug=slug)
        user_score = Participant.objects.get(user=request.user, tournament=tournament).score
        predictions = Prediction.objects.filter(user=request.user,
                                                match__tournament=tournament
                                                ).order_by('-match__kick_off')

    current_site = get_current_site(request)
    template = loader.get_template('predictions.html')
    context = {
        'site_name': current_site.name,
        'other_user': other_user,
        'user_score': user_score,
        'TOURNAMENT': tournament,
        'predictions': predictions,
        'is_participant': is_participant,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
    }
    return HttpResponse(template.render(context, request))


@login_required
def table(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)
    try:
        participant = Participant.objects.get(tournament=tournament, user=request.user)
        is_participant = True
    except Participant.DoesNotExist:
        if not tournament.is_closed():
            return redirect("competition:join", slug=slug)
        is_participant = False

    if is_participant:
        competitions = participant.competition_set.all()
    else:
        competitions = None

    participant_list = Participant.objects.filter(tournament=tournament).order_by('score')
    paginator = Paginator(participant_list, 20, orphans=5)
    page = request.GET.get('page')
    predictors = paginator.get_page(page)

    leaderboard = []
    for predictor in predictors:
        leaderboard.append((predictor.get_url(),
                            predictor.get_name(),
                            predictor.score,
                            predictor.margin_per_match,
                            predictor.get_predictions().filter(match__score__isnull=False).order_by('-match__kick_off')[:5]
                            ))

    current_site = get_current_site(request)
    template = loader.get_template('table.html')
    context = {
        'site_name': current_site.name,
        'leaderboard': leaderboard,
        'TOURNAMENT': tournament,
        'is_participant': is_participant,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
        'participants': predictors,
        'competitions': competitions,
        'has_benchmark': tournament.benchmark_set.count(),
    }
    return HttpResponse(template.render(context, request))


@login_required
def org_table(request, slug, org_name):
    tournament = get_object_or_404(Tournament, slug=slug)
    participant = get_object_or_404(Participant, tournament=tournament, user=request.user)
    try:
        comp = participant.competition_set.get(organisation__name=org_name)
        competitions = participant.competition_set.all().exclude(pk=comp.pk)
        competitions = [comp] + [c for c in competitions]
    except Competition.DoesNotExist:
        raise Http404("Organisation does not exist")

    participant_list = comp.participants.order_by('score')
    paginator = Paginator(participant_list, 20, orphans=5)
    page = request.GET.get('page')
    participants = paginator.get_page(page)

    current_site = get_current_site(request)
    template = loader.get_template('org_table.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT': tournament,
        'is_participant': True,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
        'participants': participants,
        'competitions': competitions,
    }
    return HttpResponse(template.render(context, request))


@login_required
def join(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)

    if tournament.is_closed():
        return redirect("competition:table", slug=slug)

    if request.method == 'POST':
        try:
            Participant.objects.create(user=request.user, tournament=tournament)
            messages.success(request, _("You have joined the competition"))
        except IntegrityError:
            pass
        return redirect('competition:submit', slug=slug)

    bonus = float(tournament.bonus)

    current_site = get_current_site(request)
    template = loader.get_template('join.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT': tournament,
        'draw_bonus_value': tournament.bonus * tournament.draw_bonus,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
        'example_scores': [
            (1 - bonus),
            (2 - bonus),
            (0.5 - bonus),
            (19.5 - (3 * bonus + bonus * float(tournament.draw_bonus))),
        ],
    }
    return HttpResponse(template.render(context, request))


@permission_required('competition.change_match')
def results(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)

    is_participant = True
    if not tournament.participants.filter(pk=request.user.pk).exists():
        is_participant = False

    fixture_list = Match.objects.filter(tournament=tournament,
                                        kick_off__lt=timezone.now(),
                                        score__isnull=True,
                                        home_team__isnull=False,
                                        away_team__isnull=False,
                                        postponed=False,
                                        ).order_by('kick_off')

    if request.method == 'POST':
        submited = 0
        for match in fixture_list:
            try:
                match.score = decimal.Decimal(float(request.POST[str(match.pk)]))
                fixture_list = fixture_list.exclude(pk=match.pk)
                match.save()
                submited += 1
            except (ValueError, KeyError):
                pass
        messages.add_message(request,
                             messages.SUCCESS if submited else messages.ERROR,
                             _("%d result" % submited + pluralize(submited) + " submited"))

    current_site = get_current_site(request)
    template = loader.get_template('match_results.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT': tournament,
        'fixture_list': fixture_list,
        'is_participant': is_participant,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
    }
    return HttpResponse(template.render(context, request))


@login_required
def rules(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)

    is_participant = True
    if not tournament.participants.filter(pk=request.user.pk).exists():
        if tournament.state == Tournament.ACTIVE:
            return redirect("competition:join", slug=slug)
        is_participant = False

    bonus = float(tournament.bonus)

    current_site = get_current_site(request)
    template = loader.get_template('display_rules.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT': tournament,
        'draw_bonus_value': tournament.bonus * tournament.draw_bonus,
        'is_participant': is_participant,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
        'example_scores': [
            (1 - bonus),
            (2 - bonus),
            (0.5 - bonus),
            (19.5 - (3 * bonus + bonus * float(tournament.draw_bonus))),
        ],
    }
    return HttpResponse(template.render(context, request))


@login_required
def match(request, match_pk):
    match = get_object_or_404(Match, pk=match_pk)

    if not match.tournament.participants.filter(pk=request.user.pk).exists():
        raise Http404("User is not a Participant")

    show_benchmarks = False

    if match.has_started():
        if match.score is None:
            prediction_list = match.prediction_set.all().order_by('-prediction')
        else:
            show_benchmarks = request.GET.get('benchmarks')

            if show_benchmarks:
                prediction_list = sorted(
                    chain(
                        match.prediction_set.all(),
                        match.benchmarkprediction_set.all()),
                    key=lambda obj: obj.score)
            else:
                prediction_list = match.prediction_set.all().order_by('score')

        paginator = Paginator(prediction_list, 20, orphans=5)
        predictions = paginator.get_page(request.GET.get('page'))
    else:
        predictions = None

    try:
        user_prediction = match.prediction_set.get(user=request.user)
    except Prediction.DoesNotExist:
        user_prediction = None

    current_site = get_current_site(request)
    template = loader.get_template('match.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT': match.tournament,
        'is_participant': True,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
        'predictions': predictions,
        'match': match,
        'prediction': user_prediction,
        'show_benchmarks': show_benchmarks,
        'has_benchmark': match.tournament.benchmark_set.count(),
    }
    return HttpResponse(template.render(context, request))


@login_required
def benchmark_table(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)

    try:
        Participant.objects.get(tournament=tournament, user=request.user)
    except Participant.DoesNotExist:
        return redirect("competition:join", slug=slug)

    participant_list = tournament.participant_set.all()
    benchmark_list = tournament.benchmark_set.all()

    sorted_list = sorted(chain(participant_list,
                               benchmark_list),
                         key=lambda obj: obj.score or 0)

    paginator = Paginator(sorted_list, 20, orphans=5)
    page = request.GET.get('page')
    predictors = paginator.get_page(page)

    leaderboard = []
    for predictor in predictors:
        leaderboard.append((predictor.get_url(),
                            predictor.get_name(),
                            predictor.score,
                            predictor.margin_per_match,
                            predictor.get_predictions().filter(match__score__isnull=False).order_by('-match__kick_off')[:5]
                            ))

    current_site = get_current_site(request)
    template = loader.get_template('table.html')
    context = {
        'site_name': current_site.name,
        'leaderboard': leaderboard,
        'TOURNAMENT': tournament,
        'is_participant': True,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
        'participants': predictors,
    }
    return HttpResponse(template.render(context, request))


@login_required
def benchmark(request, benchmark_pk):
    benchmark = get_object_or_404(Benchmark, pk=benchmark_pk)
    tournament = benchmark.tournament

    if not tournament.participants.filter(pk=request.user.pk).exists():
        raise Http404("User is not a Participant")

    predictions = benchmark.benchmarkprediction_set.filter(
        match__kick_off__lt=timezone.now(),
        match__postponed=False).order_by('-match__kick_off')

    current_site = get_current_site(request)
    template = loader.get_template('predictions.html')
    context = {
        'site_name': current_site.name,
        'other_user': 'Benchmark "%s"' % benchmark.name,
        'user_score': benchmark.score,
        'TOURNAMENT': tournament,
        'predictions': predictions,
        'is_participant': True,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
    }
    return HttpResponse(template.render(context, request))


@login_required
def tournament_list_open(request):
    context = {
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
    }
    return render(request, 'partial/tournament_list_open.html', context)


@login_required
def tournament_list_closed(request):
    context = {
        'closed_tournaments': Tournament.objects.filter(state=Tournament.FINISHED).order_by('-pk'),
    }
    return render(request, 'partial/tournament_list_closed.html', context)


@login_required
def match_list_todaytomorrow(request):
    user_tourns = Tournament.objects.filter(state=Tournament.ACTIVE,
                                            participant__user=request.user)

    today = datetime.date.today()
    matches_today = Match.objects.filter(
            tournament__in=user_tourns,
            kick_off__year=today.year,
            kick_off__month=today.month,
            kick_off__day=today.day,
            postponed=False
            ).order_by('kick_off')

    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    matches_tomorrow = Match.objects.filter(
            tournament__in=user_tourns,
            kick_off__year=tomorrow.year,
            kick_off__month=tomorrow.month,
            kick_off__day=tomorrow.day,
            postponed=False
            ).order_by('kick_off')

    matches_predicted = list(chain(
        matches_today.filter(prediction__user=request.user),
        matches_tomorrow.filter(prediction__user=request.user)))

    context = {
        'matches_today': matches_today,
        'matches_tomorrow': matches_tomorrow,
        'matches_predicted': matches_predicted,
        }
    return render(request, 'partial/match_list_todaytomorrow.html', context)


@login_required
def prediction_create(request, match_pk):
    match = get_object_or_404(Match,
                              pk=match_pk,
                              kick_off__gt=timezone.now())
    context = {
        'htmx': True,
        'match': match
        }
    match_view = request.GET.get('match_view', False)

    template_name = 'partial/prediction_create.html'
    if request.method == 'POST':
        try:
            prediction = Prediction(user=request.user, match=match,
                    prediction=float(request.POST['prediction_prediction']))
            prediction.save()
            context['prediction'] = prediction
            messages.success(request, _("prediction created"))
            template_name = 'partial/messages.html'
        except (KeyError, ValueError):
            # messages.error(request, _("prediction failed to be created"))
            context['error'] = True
        except IntegrityError:
            messages.error(request, _("Match has already been predicted"))
            template_name = 'partial/messages.html'

    if match_view:
        template_name = 'partial/match_prediction_form.html'

    return render(request, template_name, context)


@login_required
def prediction_update(request, prediction_pk):
    prediction = get_object_or_404(Prediction,
                                   pk=prediction_pk,
                                   user=request.user,
                                   match__kick_off__gt=timezone.now())

    template_name = 'partial/prediction_update.html'

    if request.method == 'POST':
        try:
            prediction_prediction = float(request.POST['prediction_prediction'])
            if prediction.prediction != prediction_prediction:
                prediction.prediction = prediction_prediction
                prediction.save()
                # messages.success(request, _("prediction updated"))
        except (KeyError, ValueError):
            # messages.error(request, _("prediction failed to be updated"))
            pass

    match_view = request.GET.get('match_view', False)

    if match_view:
        template_name = 'partial/match_prediction_form.html'

    context = {
        'match': prediction.match,
        'prediction': prediction,
        'is_participant': True,
        }
    return render(request, template_name, context)
