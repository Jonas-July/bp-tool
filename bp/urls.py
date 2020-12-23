from django.urls import path

from bp.views import IndexView, ProjectListView

app_name = "bp"

urlpatterns = [
    path('', IndexView.as_view(), name="index"),
    path('projects/', ProjectListView.as_view(), name="project_list"),
]
