from django.urls import path
from .views import NarrativeListView, TimelineView, NarrativeClusterListView

urlpatterns = [
    path('narratives/', NarrativeListView.as_view(), name='narrative-list'),
    path('timeline/', TimelineView.as_view(), name='timeline'),
    path('clusters/', NarrativeClusterListView.as_view(), name='narrative-cluster-list'),
]