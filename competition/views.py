from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import IntegrityError

from .models import Tournament, Match, Prediction, Participant


@login_required
def index(request):
    template = loader.get_template('index.html')
    context = {
        'all_tournaments': Tournament.objects.all(),
    }
    return HttpResponse(template.render(context, request))


@login_required
def submit(request, tour_name):
    try:
        tournament = Tournament.objects.get(name=tour_name)
    except Tournament.DoesNotExist:
        raise Http404("Tournament does not exist")

    if tournament.state == 2:
        return redirect("competition:table", tour_name=tour_name) 

    if not tournament.participants.filter(pk=request.user.pk).exists():
        return redirect("competition:join", tour_name=tour_name) 

    fixture_list = Match.objects.filter(tournament=tournament, kick_off__gt=timezone.now())

    if request.method == 'POST':
        for match in fixture_list:
            if str(match.pk) in request.POST:
                if request.POST[str(match.pk)]:
                    Prediction(user=request.user, match=match, prediction=float(request.POST[str(match.pk)])).save()

    for prediction in Prediction.objects.filter(user=request.user):
        if prediction.match in fixture_list:
            fixture_list = fixture_list.exclude(pk=prediction.match.pk)


    template = loader.get_template('submit.html')
    context = {
        'TOURNAMENT' : tournament,
        'fixture_list': fixture_list,
        'is_participant': True,
    }
    return HttpResponse(template.render(context, request))


@login_required
def predictions(request, tour_name):
    try:
        tournament = Tournament.objects.get(name=tour_name)
    except Tournament.DoesNotExist:
        raise Http404("Tournament does not exist")

    is_participant = True
    if not tournament.participants.filter(pk=request.user.pk).exists():
        if tournament.state != 2:
            return redirect("competition:table", tour_name=tour_name)
        is_participant = False

    other_user = None
    user_score = None

    if request.GET:
        try:
            other_user = User.objects.get(username=request.GET['user'])
            if other_user == request.user:
                other_user = None
            else:
                predictions = Prediction.objects.filter(user=other_user, match__tournament=tournament, match__kick_off__lt=timezone.now()).order_by('match_id')
                if other_user.first_name and other_user.last_name:
                    other_user = "%s %s" % (other_user.first_name, other_user.last_name)
                else:
                    other_user = other_user.username
        except User.DoesNotExist:
            print("User(%s) tried to look at %s's predictions but '%s' does not exist"
                  % (request.user, request.GET['user'], request.GET['user']))

    if not other_user:
        if not is_participant:
            return redirect("competition:table", tour_name=tour_name)
        user_score = Participant.objects.get(user=request.user, tournament=tournament).score
        predictions = Prediction.objects.filter(user=request.user, match__tournament=tournament).order_by('match_id')

    template = loader.get_template('predictions.html')
    context = {
        'other_user': other_user,
        'user_score': user_score,
        'TOURNAMENT': tournament,
        'predictions': predictions,
        'is_participant': is_participant,
    }
    return HttpResponse(template.render(context, request))


@login_required
def table(request, tour_name):
    try:
        tournament = Tournament.objects.get(name=tour_name)
    except Tournament.DoesNotExist:
        raise Http404("Tournament does not exist")

    is_participant = True
    if not tournament.participants.filter(pk=request.user.pk).exists():
        if tournament.state != 2:
            return redirect("competition:join", tour_name=tour_name) 
        is_participant = False

    leaderboard = []
    for participant in Participant.objects.filter(tournament=tournament).order_by('score'):
        name = "%s %s" % (participant.user.first_name, participant.user.last_name)
        if name == " ":
            name = participant.user.username
        leaderboard.append((participant.user.username, name, participant.score))


    template = loader.get_template('table.html')
    context = {
        'leaderboard': leaderboard,
        'TOURNAMENT': tournament,
        'is_participant': is_participant,
    }
    return HttpResponse(template.render(context, request))


@login_required
def join(request, tour_name):
    try:
        tournament = Tournament.objects.get(name=tour_name)
    except Tournament.DoesNotExist:
        raise Http404("Tournament does not exist")

    if request.method == 'POST':
        try:
            Participant(user=request.user, tournament=tournament).save()
        except IntegrityError:
            pass
        return redirect('competition:submit' , tour_name=tour_name)

    template = loader.get_template('join.html')
    context = {
        'TOURNAMENT': tournament,
        'draw_bonus_value': tournament.bonus * tournament.draw_bonus,
    }
    return HttpResponse(template.render(context, request))

