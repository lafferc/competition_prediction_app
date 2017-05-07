from django.contrib import admin
from competition.models import Team, Tournament, Match, Prediction, Participant
from competition.models import Sport
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
    readonly_fields = ('score',)

    def has_delete_permission(self, request, obj=None):
        return False


def pop_leaderboard(modeladmin, request, queryset):
    g_logger.debug("pop_leaderboard(%r, %r, %r)", modeladmin, request, queryset)
    for tournament in queryset:
        tournament.update_table()


def close_tournament(modeladmin, request, queryset):
    g_logger.debug("close_tournament(%r, %r, %r)", modeladmin, request, queryset)
    for tournament in queryset:
        tournament.close(request)


def open_tournament(modeladmin, request, queryset):
    g_logger.debug("open_tournament(%r, %r, %r)", modeladmin, request, queryset)
    for tournament in queryset:
        tournament.open(request)


class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = ( ParticipantInline, )
    actions = [pop_leaderboard, close_tournament, open_tournament]
    list_filter = (
        ('sport', admin.RelatedOnlyFieldListFilter),
        "state",
        "year",
    )
    fieldsets = (
        (None, {
            'fields': ('name', 'sport', 'state', 'bonus', 'draw_bonus', 'late_get_bonus', 'year',
                       'winner', 'add_matches', 'display_margin_per_game')
        }),
    )

    def get_readonly_fields(self, request, obj):
        if obj:
            return ('sport', 'bonus', 'late_get_bonus', 'draw_bonus', 'winner', 'state')
        return ('winner')

    def get_fieldsets(self, request, obj):
        if request.user.has_perm('Tournament.csv_upload') and (not obj or obj.state not in [2, 3]):
            return self.fieldsets
        return ((None, {'fields': ('name', 'sport', 'state', 'bonus', 'draw_bonus',
                                   'late_get_bonus', 'year', 'winner')}),)


def calc_match_result(modeladmin, request, queryset):
    tourns = []
    for match in queryset:
        if match.score is None:
            continue
        if match.tournament not in tourns:
            g_logger.info("adding %s to list" % match.tournament)
            tourns.append(match.tournament)
        match.check_predictions()
    for tourn in tourns:
        tourn.update_table()


class MatchAdmin(admin.ModelAdmin):
    list_display = ('match_id', 'home_team', 'away_team', 'kick_off', 'score')
    list_filter = (
        ('tournament', admin.RelatedOnlyFieldListFilter),
    )
    actions = [calc_match_result]
    fieldsets = (
        (None, {
            'fields': ('tournament', 'match_id', 'home_team', 'home_team_winner_of',
                       'away_team', 'away_team_winner_of', 'kick_off', 'score')
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
            return ( (None, { 'fields': ('tournament', 'match_id', 'home_team',
                                         'home_team_winner_of', 'away_team', 'kick_off', 'score')
                            }),)
        if not obj.away_team:
            return ( (None, { 'fields': ('tournament', 'match_id', 'home_team', 'away_team',
                                         'away_team_winner_of', 'kick_off', 'score') }),)
        return ( (None, { 'fields': ('tournament', 'match_id', 'home_team', 'away_team', 'kick_off', 'score') }),)


class PredictionAdmin(admin.ModelAdmin):
    list_display = ('user', 'match', 'entered')
    readonly_fields = ('score', "late")

    list_filter = (
        ('match', admin.RelatedOnlyFieldListFilter),
        ('user', admin.RelatedOnlyFieldListFilter),
        'match__tournament',
    )


admin.site.register(Sport)
admin.site.register(Team, TeamAdmin)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Prediction, PredictionAdmin)
