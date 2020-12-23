from django.urls import path

from bp.views import IndexView, ProjectListView, ProjectView, TLView, TLListView

app_name = "bp"

urlpatterns = [
    path('', IndexView.as_view(), name="index"),
    path('project/', ProjectListView.as_view(), name="project_list"),
    path('project/<pk>/', ProjectView.as_view(), name="project_detail"),
    path('tl/', TLListView.as_view(), name="tl_list"),
    path('tl/<pk>/', TLView.as_view(), name="tl_detail"),
]
