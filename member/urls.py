from django.conf.urls import url
from . import views

app_name = "member"

urlpatterns = [
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^use_token/$', views.use_token, name='use_token'),
    url(r'^announcement/$', views.announcement, name='announcement'),
    url(r'^competition/(?P<comp_pk>[0-9]+)/$', views.print_tickets, name='tickets'),
]
