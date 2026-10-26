"""test_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.urls import include, re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^competition/', include('competition.urls', namespace="competition")),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^accounts/', include('allauth.urls')),
    re_path(r'^accounts/', include('member.urls', namespace="member")),
    re_path(r'^about/', views.about, name='about'),
    re_path(r'^gdpr/', views.gdpr, name='gdpr'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
