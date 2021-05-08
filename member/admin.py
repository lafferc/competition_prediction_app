from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from member.models import Profile, Organisation, Competition, Ticket

import logging

g_logger = logging.getLogger(__name__)


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    readonly_fields = ('used', 'token')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class ParticipantInline(admin.TabularInline):
    model = Competition.participants.through
    extra = 0

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):

        field = super(ParticipantInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'participant':
            if request._obj_ is not None:
                field.queryset = field.queryset.filter(tournament=request._obj_.tournament)
            else:
                field.queryset = field.queryset.none()

        return field


def add_tickets(modeladmin, request, queryset):
    g_logger.debug("add_tickets(%r, %r, %r)", modeladmin, request, queryset)
    for comp in queryset:
        for i in range(10):
            Ticket.objects.create(competition=comp)


class CompetitionAdmin(admin.ModelAdmin):
    inlines = (TicketInline, ParticipantInline)
    actions = [add_tickets]
    list_display = ('organisation', 'tournament', 'participant_count')
    fields = ('organisation', 'tournament', 'token_len')

    def participant_count(self, obj):
        return obj.participants.count()

    def get_readonly_fields(self, request, obj):
        return obj and ('organisation', 'tournament') or []

    def get_inline_instances(self, request, obj=None):
        return obj and super(CompetitionAdmin, self).get_inline_instances(request, obj) or []

    def get_form(self, request, obj=None, **kwargs):
        # save obj reference for future processing in Inline
        request._obj_ = obj
        return super(CompetitionAdmin, self).get_form(request, obj, **kwargs)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'test_features_enabled')


class CustomUserAdmin(UserAdmin):
    actions = ['merge_users']

    def merge_users(self, request, queryset):
        if 'apply' in request.POST:
            # The user clicked submit on the intermediate form.
            # Perform our update action:

            # Redirect to our admin view after our update has 
            # completed with a nice little info message saying 
            # our models have been updated:
            self.message_user(request,
                              "Merged {} users".format(queryset.count()))
            return HttpResponseRedirect(request.get_full_path())
        # TODO get list of tourns and count of matches

        return render(request,
                      'admin/merge_users.html',
                      context={'users':queryset})



admin.site.register(Profile)
admin.site.register(Organisation)
admin.site.register(Competition, CompetitionAdmin)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
