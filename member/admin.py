from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render
from allauth.socialaccount.models import SocialApp
from member.models import Profile, Organisation, Competition, Ticket
from member.forms import UserMergeForm, ProfileMergeForm

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


class CompetitionAdmin(admin.ModelAdmin):
    inlines = (TicketInline, ParticipantInline)
    actions = ["add_tickets"]
    list_display = ('organisation', 'tournament', 'participant_count')
    fields = ('organisation', 'tournament', 'token_len')
    list_filter = [
            ('organisation', admin.RelatedOnlyFieldListFilter),
            ('tournament', admin.RelatedOnlyFieldListFilter),
            ]

    def get_queryset(self, request):
        from django.db.models import Count
        qs = super().get_queryset(request)
        qs = qs.annotate(Count('participants'))
        return qs

    def participant_count(self, obj):
        return obj.participants__count
    participant_count.admin_order_field = 'participants__count'

    def get_readonly_fields(self, request, obj):
        return obj and ('organisation', 'tournament') or []

    def get_inline_instances(self, request, obj=None):
        return obj and super(CompetitionAdmin, self).get_inline_instances(request, obj) or []

    def get_form(self, request, obj=None, **kwargs):
        # save obj reference for future processing in Inline
        request._obj_ = obj
        return super(CompetitionAdmin, self).get_form(request, obj, **kwargs)

    def add_tickets(self, request, queryset):
        g_logger.debug("add_tickets(%r, %r, %r)", self, request, queryset)
        for comp in queryset:
            for i in range(10):
                Ticket.objects.create(competition=comp)
    add_tickets.allowed_permissions = ('add',)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user__id', 'test_features_enabled')
    actions = ["display_social_names"]
    list_filter = ["test_features_enabled", "user__is_staff", "user__last_login"]

    def user__id(self, obj):
        return obj.user.id
    user__id.admin_order_field = 'user__id'

    def get_search_fields(self, request):
        return ['user__' + f for f in UserAdmin.search_fields]

    def display_social_names(self, request, queryset):
        info = {}
        for s_app in SocialApp.objects.all():
            info[s_app.provider] = [(p, p.get_social_name(s_app.provider)) for p in queryset]

        return render(request,
                      'admin/social_display_names.html',
                      context={'info': info})


class CustomUserAdmin(UserAdmin):
    actions = ['merge_users']
    list_filter = UserAdmin.list_filter + ("last_login",)

    def merge_users(self, request, queryset):
        primary_user = queryset[0]
        other_users = queryset[1:]

        if not other_users:
            self.message_user(request,
                              "Not enough users to merge",
                              level="error")
            return HttpResponseRedirect(request.get_full_path())

        profiles = Profile.objects.filter(user__in=queryset)

        if 'apply' in request.POST:
            # The user clicked submit on the intermediate form.
            # Perform our update action:

            user_form = UserMergeForm(request.POST, instance=primary_user)
            user_form.add_choices(queryset)

            profile_form = ProfileMergeForm(request.POST, instance=primary_user.profile)

            if user_form.is_valid() and profile_form.is_valid() and False:

                # TODO merge accounts

                # Redirect to our admin view after our update has 
                # completed with a nice little info message saying 
                # our models have been updated:
                self.message_user(request,
                                  "Merged {} users".format(queryset.count()))
                return HttpResponseRedirect(request.get_full_path())

        else:
            user_form = UserMergeForm(instance=primary_user)
            user_form.add_choices(queryset)
            profile_form = ProfileMergeForm(instance=primary_user.profile)
            # profile_form.merge_values(profiles)
        
        # TODO add inlineformset_factory for emails
        # EmailFormset = inlineformset_factory(EmailAddress, User)
        # email_formset = EmailFormset(instance=primary_user)

        tourn_dict = {}
        for user in queryset:
            for tourn in user.tournament_set.all():
                predictions_all = user.prediction_set.filter(match__tournament=tourn).count()
                predictions_late = user.prediction_set.filter(match__tournament=tourn, late=True).count()
                if tourn not in tourn_dict:
                    tourn_dict[tourn] = []
                tourn_dict[tourn].append((user, predictions_all, predictions_late))

        context = {
            'users':queryset,
            'tourn_dict': tourn_dict,
            'opts': self.model._meta,
            'media': self.media,
            'user_form': user_form,
            'profile_form': profile_form,
            }

        return render(request,
                      'admin/merge_users.html',
                      context=context)


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Organisation)
admin.site.register(Competition, CompetitionAdmin)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
