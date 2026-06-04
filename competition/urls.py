from django.conf.urls import re_path

from . import views

app_name = "competition"

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^match/(?P<match_pk>[0-9]+)/$', views.match, name='match'),
    re_path(r'^match/(?P<match_pk>[0-9]+)/predict/$', views.prediction_create, name='prediction_create'),
    re_path(r'^benchmark/(?P<benchmark_pk>[0-9]+)/$', views.benchmark, name='benchmark'),
    re_path(r'^(?P<slug>[-\w]+)/$', views.submit, name='submit'),
    re_path(r'^(?P<slug>[-\w]+)/predictions/$', views.predictions, name='predictions'),
    re_path(r'^(?P<slug>[-\w]+)/table/$', views.table, name='table'),
    re_path(r'^(?P<slug>[-\w]+)/table/(?P<org_name>[^/]+)/$', views.org_table, name='org_table'),
    re_path(r'^(?P<slug>[-\w]+)/join/$', views.join, name='join'),
    re_path(r'^(?P<slug>[-\w]+)/results/$', views.results, name='results'),
    re_path(r'^(?P<slug>[-\w]+)/rules/$', views.rules, name='rules'),
    re_path(r'^(?P<slug>[-\w]+)/benchmark/$', views.benchmark_table, name='benchmark_table'),
    re_path(r'^tournament_list/open/$', views.tournament_list_open, name='tournament_list_open'),
    re_path(r'^tournament_list/closed/$', views.tournament_list_closed, name='tournament_list_closed'),
    re_path(r'^match_list/todaytomorrow/$', views.match_list_todaytomorrow, name='match_list_todaytomorrow'),
    re_path(r'^prediction/(?P<prediction_pk>[0-9]+)/edit/$', views.prediction_update, name='prediction_update'),
]
