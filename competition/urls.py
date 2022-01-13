from django.conf.urls import url

from . import views

app_name = "competition"

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^match/(?P<match_pk>[0-9]+)/$', views.match, name='match'),
    url(r'^match/(?P<match_pk>[0-9]+)/predict/$', views.prediction_create, name='prediction_create'),
    url(r'^benchmark/(?P<benchmark_pk>[0-9]+)/$', views.benchmark, name='benchmark'),
    url(r'^(?P<tour_name>[^/]+)/$', views.submit, name='submit'),
    url(r'^(?P<tour_name>[^/]+)/predictions/$', views.predictions, name='predictions'),
    url(r'^(?P<tour_name>[^/]+)/table/$', views.table, name='table'),
    url(r'^(?P<tour_name>[^/]+)/table/(?P<org_name>[^/]+)/$', views.org_table, name='org_table'),
    url(r'^(?P<tour_name>[^/]+)/join/$', views.join, name='join'),
    url(r'^(?P<tour_name>[^/]+)/results/$', views.results, name='results'),
    url(r'^(?P<tour_name>[^/]+)/rules/$', views.rules, name='rules'),
    url(r'^(?P<tour_name>[^/]+)/benchmark/$', views.benchmark_table, name='benchmark_table'),
    url(r'^tournament_list/open/$', views.tournament_list_open, name='tournament_list_open'),
    url(r'^tournament_list/closed/$', views.tournament_list_closed, name='tournament_list_closed'),
    url(r'^match_list/todaytomorrow/$', views.match_list_todaytomorrow, name='match_list_todaytomorrow'),
    url(r'^prediction/(?P<prediction_pk>[0-9]+)/edit/$', views.prediction_update, name='prediction_update'),
]
