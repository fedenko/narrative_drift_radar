from django.urls import path
from . import views

urlpatterns = [
    path('articles/', views.ArticleListView.as_view(), name='article-list'),
    path('reports/weekly/', views.weekly_reports, name='weekly-reports'),
]