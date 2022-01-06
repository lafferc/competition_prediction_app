from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string, get_template
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext as _
import datetime
from itertools import chain

from competition.models import Tournament, Match


@login_required
def index(request):
    current_site = get_current_site(request)

    context = {
        'site_name': current_site.name,
    }
    return render(request, 'home.html', context)


def about(request):
    current_site = get_current_site(request)
    template = get_template('about.html')

    context = {
        'site_name': current_site.name,
    }
    return HttpResponse(template.render(context, request))


def gdpr(request):
    current_site = get_current_site(request)
    template = get_template('gdpr.html')

    context = {
        'site_name': current_site.name,
    }
    return HttpResponse(template.render(context, request))
