from django.contrib import admin
from django.db.models import Avg, Sum, F
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from competition.models import Team, Tournament, Match, Prediction, Participant
from competition.models import Sport, Benchmark, BenchmarkPrediction
import logging

g_logger = logging.getLogger(__name__)


class TeamInline(admin.TabularInline):
    model = Team
    extra = 0


class SportAdmin(admin.ModelAdmin):
    inlines = (TeamInline,)


class BenchmarkInline(admin.TabularInline):
    model = Benchmark
    extra = 0
    fields = ('name', 'score', 'margin_per_match')
    readonly_fields = ('name', 'score', 'margin_per_match')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'participant_count', 'match_count')
    inlines = (BenchmarkInline, )
    actions = ['pop_leaderboard', 'close_tournament',
               'open_tournament', 'archive_tournament']
    list_filter = (
        ('sport', admin.RelatedOnlyFieldListFilter),
        "state",
        "year",
    )
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'sport', 'state', 'bonus', 'draw_bonus', 'year',
                       'winner', 'add_matches', 'test_features_enabled', 'draw_definition',
                       'additional_rules')
        }),
    )
    prepopulated_fields = {"slug": ("name",)}

    def get_readonly_fields(self, request, obj):
        if obj:
            return ('sport', 'bonus', 'draw_bonus',
                    'winner', 'state', 'year', 'test_features_enabled')
        return ('winner')

    def get_fieldsets(self, request, obj):
        if request.user.has_perm('Tournament.csv_upload'):
            if not obj or obj.state not in [Tournament.FINISHED, Tournament.ARCHIVED]:
                return self.fieldsets
        return ((None, {'fields': ('name', 'slug', 'sport', 'state', 'bonus', 'draw_bonus',
                                   'year', 'winner', 'draw_definition', 'additional_rules')}),)

    def get_queryset(self, request):
        from django.db.models import Count
        qs = super().get_queryset(request)
        qs = qs.annotate(Count('participants'))
        return qs

    def participant_count(self, obj):
        return obj.participants__count
    participant_count.admin_order_field = 'participants__count'

    def match_count(self, obj):
        return obj.match_set.count()

    def get_inline_instances(self, request, obj=None):
        return obj and super(TournamentAdmin, self).get_inline_instances(request, obj) or []

    def pop_leaderboard(self, request, queryset):
        g_logger.debug("pop_leaderboard(%r, %r, %r)", self, request, queryset)
        for tournament in queryset:
            tournament.update_table()
    pop_leaderboard.allowed_permissions = ('change',)

    def close_tournament(self, request, queryset):
        g_logger.debug("close_tournament(%r, %r, %r)", self, request, queryset)
        for tournament in queryset:
            tournament.close(request)
    close_tournament.allowed_permissions = ('change',)

    def open_tournament(self, request, queryset):
        g_logger.debug("open_tournament(%r, %r, %r)", self, request, queryset)
        for tournament in queryset:
            tournament.open(request)
    open_tournament.allowed_permissions = ('change',)

    def archive_tournament(self, request, queryset):
        queryset.update(state=Tournament.ARCHIVED)
    archive_tournament.allowed_permissions = ('change',)


class MatchAdmin(admin.ModelAdmin):
    list_display = ('match_id', 'home_team', 'away_team', 'kick_off', 'postponed', 'score')
    list_filter = [
        "postponed",
        'kick_off',
        ('tournament__sport', admin.RelatedOnlyFieldListFilter),
        ('tournament', admin.RelatedOnlyFieldListFilter),
    ]
    actions = ['calc_match_result', 'postpone', 'show_top_ten', 'swap_home_and_away']
    fieldsets = (
        (None, {
            'fields': ('tournament', 'match_id', 'home_team', 'home_team_winner_of',
                       'away_team', 'away_team_winner_of', 'kick_off', 'postponed', 'score')
        }),
    )
    search_fields = ['home_team__name', 'away_team__name']

    def get_readonly_fields(self, request, obj):
        if not obj:
            return ('score',)
        if obj.home_team and obj.away_team:
            return ('tournament', 'match_id', 'home_team', 'away_team')
        return ('tournament', 'match_id', 'score',)

    def get_fieldsets(self, request, obj):
        if not obj:
            return self.fieldsets
        if not obj.home_team and not obj.away_team:
            return self.fieldsets
        if not obj.home_team:
            return ((None, {'fields': ('tournament', 'match_id', 'home_team',
                                       'home_team_winner_of', 'away_team',
                                       'kick_off', 'postponed', 'score')
                            }),)
        if not obj.away_team:
            return ((None, {'fields': ('tournament', 'match_id', 'home_team',
                                       'away_team', 'away_team_winner_of',
                                       'kick_off', 'postponed', 'score')}),)
        return ((None, {'fields': ('tournament', 'match_id', 'home_team',
                                   'away_team', 'kick_off', 'postponed',
                                   'score')}),)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tournament":
            kwargs["queryset"] = Tournament.objects.filter(state__in=[Tournament.PENDING,
                                                                      Tournament.ACTIVE])
        if db_field.name in ["home_team_winner_of", "away_team_winner_of"]:
            kwargs["queryset"] = Match.objects.filter(
                tournament__state__in=[Tournament.PENDING, Tournament.ACTIVE]
            ).filter(score=None)
        return super(MatchAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def calc_match_result(self, request, queryset):
        for match in queryset:
            if match.score is None:
                continue
            match.tournament.check_predictions(match)
    calc_match_result.allowed_permissions = ('change',)

    def postpone(self, request, queryset):
        queryset.update(postponed=True)
    postpone.allowed_permissions = ('change',)

    def show_top_ten(self, request, queryset):
        from member.forms import SocialProviderForm 
        from django.contrib.auth.models import User

        form = SocialProviderForm(request.POST)

        provider = None
        if form.is_valid():
            provider = form.cleaned_data['social_provider']
            provider = provider and provider.provider

        top_10 = (Prediction.objects.filter(match__in=queryset)
                  .values('user')
                  .annotate(Sum('score'), Avg('margin'))
                  .order_by('score__sum')[:10])

        for p in top_10:
            p['user'] = User.objects.get(pk=p['user'])
            p['social_name'] = p['user'].profile.get_social_name(provider)

        context = {
                'matches': queryset,
                'top_10': top_10,
                'form': form,
                'action': 'show_top_ten',
                }

        template = loader.select_template([f'admin/{provider}_top10.html', 
                                           'admin/top10.html'])

        return HttpResponse(template.render(context, request))
    show_top_ten.allowed_permissions = ('change',)

    def swap_home_and_away(self, request, queryset):
        queryset.update(home_team=F('away_team'),
                        away_team=F('home_team'),
                        home_team_winner_of=F('away_team_winner_of'),
                        away_team_winner_of=F('home_team_winner_of'),
                        score=F('score')*-1)
        Prediction.objects.filter(
                match__in=queryset
                ).update(prediction=F('prediction')*-1)
    swap_home_and_away.allowed_permissions = ('change',)


class PredictionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'match', 'entered')

    list_filter = (
        'match__tournament',
        ('user', admin.RelatedOnlyFieldListFilter),
        'late',
        'correct',
    )

    def get_readonly_fields(self, request, obj):
        if obj:
            return ('user', 'match', 'prediction', 'margin', 'score', "late", "correct")
        return ('margin', 'score', "late")


class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament', 'prediction_algorithm')
    fieldsets = (
        (None, {
            'fields': (
                'name', 'tournament', 'prediction_algorithm',
                'static_value', 'range_start', 'range_end')
        }),
    )

    def get_readonly_fields(self, request, obj):
        if obj:
            return ('prediction_algorithm', 'static_value', 'range_start',
                    'range_end', 'tournament', 'score', 'margin_per_match')
        return ('score', 'margin_per_match')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tournament":
            kwargs["queryset"] = Tournament.objects.filter(state__in=[Tournament.PENDING,
                                                                      Tournament.ACTIVE])
        return super(BenchmarkAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def get_fieldsets(self, request, obj):
        if not obj:
            return self.fieldsets

        if obj.prediction_algorithm == Benchmark.STATIC:
            return ((None, {'fields': (
                'name', 'tournament', 'prediction_algorithm', 'static_value',
                'score', 'margin_per_match')}),)
        elif obj.prediction_algorithm == Benchmark.MEAN:
            return ((None, {'fields': (
                'name', 'tournament', 'prediction_algorithm', 'score',
                'margin_per_match')}),)
        elif obj.prediction_algorithm == Benchmark.RANDOM:
            return ((None, {'fields': (
                'name', 'tournament', 'prediction_algorithm', 'range_start',
                'range_end', 'score', 'margin_per_match')}),)


class TeamAdmin(admin.ModelAdmin):
    model = Team
    actions = ['merge']

    def merge(self, request, queryset):
        #TODO use confirm screen
        g_logger.debug("Attempting to merge %s", queryset)
        primary_team = queryset[0]
        secondary_teams = queryset[1:]

        for team in secondary_teams:
            g_logger.debug("Merging %s into %s", team, primary_team)

            Match.objects.filter(home_team=team).update(home_team=primary_team)
            Match.objects.filter(away_team=team).update(away_team=primary_team)

            g_logger.debug("Deleting %s", team)
            team.delete()


    merge.allowed_permissions = ('change','delete')




admin.site.register(Sport, SportAdmin)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Prediction, PredictionAdmin)
admin.site.register(Benchmark, BenchmarkAdmin)
admin.site.register(BenchmarkPrediction)
admin.site.register(Team, TeamAdmin)
