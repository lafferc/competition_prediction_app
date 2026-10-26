from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site


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
