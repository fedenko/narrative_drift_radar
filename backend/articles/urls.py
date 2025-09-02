from django.urls import path
from . import views

urlpatterns = [
    path('articles/', views.ArticleListView.as_view(), name='article-list'),
    path('narratives/', views.NarrativeListView.as_view(), name='narrative-list'),
    path('timeline/', views.TimelineView.as_view(), name='timeline'),
    path('clusters/', views.NarrativeClusterListView.as_view(), name='cluster-list'),
    path('reports/weekly/', views.weekly_reports, name='weekly-reports'),
]