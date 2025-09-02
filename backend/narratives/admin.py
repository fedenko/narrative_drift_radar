from django.contrib import admin
from .models import Narrative, NarrativeCluster, TimelineEvent


@admin.register(Narrative)
class NarrativeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')


@admin.register(NarrativeCluster)
class NarrativeClusterAdmin(admin.ModelAdmin):
    list_display = ('narrative', 'cluster_date', 'created_at')
    list_filter = ('narrative', 'cluster_date')
    readonly_fields = ('centroid',)


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ('narrative', 'event_type', 'event_date', 'significance_score')
    list_filter = ('event_type', 'narrative', 'event_date')
    search_fields = ('description',)
