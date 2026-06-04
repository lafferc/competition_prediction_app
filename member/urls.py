from django.conf.urls import re_path
from . import views

app_name = "member"

urlpatterns = [
    re_path(r'^profile/$', views.profile, name='profile'),
    re_path(r'^use_token/$', views.use_token, name='use_token'),
    re_path(r'^announcement/$', views.announcement, name='announcement'),
    re_path(r'^competition/(?P<comp_pk>[0-9]+)/$', views.print_tickets, name='tickets'),
]
