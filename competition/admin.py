from django.contrib import admin
from django.db.models import Avg, Sum
from django.shortcuts import render
from competition.models import Team, Tournament, Match, Prediction, Participant
from competition.models import Sport, Benchmark, BenchmarkPrediction
import logging

g_logger = logging.getLogger(__name__)


class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    list_filter = (
        ('sport', admin.RelatedOnlyFieldListFilter),
    )

    def get_readonly_fields(self, request, obj):
        if obj:
            return ('sport',)
        return ()


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0
    readonly_fields = ('user', 'score', 'margin_per_match')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


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
    inlines = (BenchmarkInline, ParticipantInline,)
    actions = ['pop_leaderboard', 'close_tournament',
               'open_tournament', 'archive_tournament']
    list_filter = (
        ('sport', admin.RelatedOnlyFieldListFilter),
        "state",
        "year",
    )
    fieldsets = (
        (None, {
            'fields': ('name', 'sport', 'state', 'bonus', 'draw_bonus', 'year',
                       'winner', 'add_matches', 'test_features_enabled', 'draw_definition')
        }),
    )

    def get_readonly_fields(self, request, obj):
        if obj:
            return ('sport', 'bonus', 'draw_bonus',
                    'winner', 'state', 'year', 'test_features_enabled')
        return ('winner')

    def get_fieldsets(self, request, obj):
        if request.user.has_perm('Tournament.csv_upload'):
            if not obj or obj.state not in [Tournament.FINISHED, Tournament.ARCHIVED]:
                return self.fieldsets
        return ((None, {'fields': ('name', 'sport', 'state', 'bonus', 'draw_bonus',
                                   'year', 'winner', 'draw_definition')}),)

    def participant_count(self, obj):
        return obj.participant_set.count()

    def match_count(self, obj):
        return obj.match_set.count()

    def get_inline_instances(self, request, obj=None):
        return obj and super(TournamentAdmin, self).get_inline_instances(request, obj) or []

    def pop_leaderboard(self, request, queryset):
        g_logger.debug("pop_leaderboard(%r, %r, %r)", self, request, queryset)
        for tournament in queryset:
            tournament.update_table()

    def close_tournament(self, request, queryset):
        g_logger.debug("close_tournament(%r, %r, %r)", self, request, queryset)
        for tournament in queryset:
            tournament.close(request)

    def open_tournament(self, request, queryset):
        g_logger.debug("open_tournament(%r, %r, %r)", self, request, queryset)
        for tournament in queryset:
            tournament.open(request)

    def archive_tournament(self, request, queryset):
        queryset.update(state=Tournament.ARCHIVED)


class MatchAdmin(admin.ModelAdmin):
    list_display = ('match_id', 'home_team', 'away_team', 'kick_off', 'postponed', 'score')
    list_filter = (
        "postponed",
        ('tournament', admin.RelatedOnlyFieldListFilter),
    )
    actions = ['calc_match_result', 'postpone', 'show_top_ten']
    fieldsets = (
        (None, {
            'fields': ('tournament', 'match_id', 'home_team', 'home_team_winner_of',
                       'away_team', 'away_team_winner_of', 'kick_off', 'postponed', 'score')
        }),
    )

    def get_readonly_fields(self, request, obj):
        if obj:
            return ('tournament', 'match_id', 'home_team', 'away_team')
        return ('score',)

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

    def postpone(self, request, queryset):
        queryset.update(postponed=True)

    def show_top_ten(self, request, queryset):

        top_10 = (Prediction.objects.filter(match__in=queryset)
                  .values('user')
                  .annotate(Sum('score'), Avg('margin'))
                  .order_by('score__sum')[:10])

        return render(request,
                      'admin/top10.html',
                      context={'matches': queryset,
                               'top_10': top_10,
                               })


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


admin.site.register(Sport)
admin.site.register(Team, TeamAdmin)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Prediction, PredictionAdmin)
admin.site.register(Benchmark, BenchmarkAdmin)
admin.site.register(BenchmarkPrediction)
