from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from allauth.socialaccount.models import SocialApp, SocialAccount
from allauth.account.models import EmailAddress
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

        tourn_dict = {}
        for user in queryset:
            for tourn in user.tournament_set.all():
                predictions_all = user.prediction_set.filter(match__tournament=tourn).count()
                predictions_late = user.prediction_set.filter(match__tournament=tourn, late=True).count()
                if tourn not in tourn_dict:
                    tourn_dict[tourn] = []
                tourn_dict[tourn].append((user, predictions_all, predictions_late))

        if 'apply' in request.POST:
            # The user clicked submit on the intermediate form.
            # Perform our update action:

            user_form = UserMergeForm(request.POST, instance=primary_user)
            user_form.add_choices(queryset)

            profile_form = ProfileMergeForm(request.POST, instance=primary_user.profile)

            if user_form.is_valid() and profile_form.is_valid():

                # TODO merge accounts

                if tourn_dict:
                    self.message_user(request,
                                      "Cannot merge users that have join tournaments",
                                      level="error")
                    return HttpResponseRedirect(request.get_full_path())


                for user in other_users:
                    user.emailaddress_set.update(user=primary_user, primary=False)

                # TODO set primary on chosen email address

                # TODO delete all other_users
                # for user in other_users:
                #    Note: this will delete all FK objects also
                #    user.delete()
                #  

                user_form.save()
                profile_form.save()

                # Redirect to our admin view after our update has 
                # completed with a nice little info message saying 
                # our models have been updated:
                self.message_user(request,
                                  "Merged {} users".format(queryset.count()))
                return HttpResponseRedirect(request.get_full_path())

        else:
            user_form = UserMergeForm(instance=primary_user)
            user_form.add_choices(queryset)


            # set starting data for form
            data = {
                    'dob': primary_user.profile.dob,
                    'can_receive_emails': primary_user.profile.can_receive_emails,
                    'email_on_new_competition': primary_user.profile.email_on_new_competition,
                    'test_features_enabled': primary_user.profile.test_features_enabled,
                    'cookie_consent': primary_user.profile.cookie_consent,
                    }

            for user in other_users:
                data['dob'] = data['dob'] or user.profile.dob
                data['can_receive_emails'] = data['can_receive_emails'] or user.profile.can_receive_emails
                data['email_on_new_competition'] = data['email_on_new_competition'] or user.profile.email_on_new_competition
                data['test_features_enabled'] = data['test_features_enabled'] or user.profile.test_features_enabled
                data['cookie_consent'] = min(data['cookie_consent'], user.profile.cookie_consent)

            profile_form = ProfileMergeForm(instance=primary_user.profile, data=data)
            # profile_form.merge_values(profiles)
        
        # TODO add inlineformset_factory for emails
        SocialAccountFormset = inlineformset_factory(get_user_model(), SocialAccount, exclude=['user'])
        EmailAddressFormset = inlineformset_factory(get_user_model(), EmailAddress, exclude=['user'], extra=0)
        email_formset = EmailAddressFormset(instance=primary_user)

        context = {
            'users':queryset,
            'tourn_dict': tourn_dict,
            'opts': self.model._meta,
            'media': self.media,
            'user_form': user_form,
            'profile_form': profile_form,
            'email_formset': email_formset,
            }

        return render(request,
                      'admin/merge_users.html',
                      context=context)


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Organisation)
admin.site.register(Competition, CompetitionAdmin)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
