from django.urls import path
from django.views.generic import TemplateView

from bp.views import IndexView, ProjectListView, ProjectView, TLView, TLListView, AGGradeView, AGGradeSuccessView, ProjectImportView

app_name = "bp"

urlpatterns = [
    path('', IndexView.as_view(), name="index"),
    path('project/', ProjectListView.as_view(), name="project_list"),
    path('project/import/', ProjectImportView.as_view(), name="project_import"),
    path('project/<pk>/', ProjectView.as_view(), name="project_detail"),
    path('tl/', TLListView.as_view(), name="tl_list"),
    path('tl/<pk>/', TLView.as_view(), name="tl_detail"),
    path('grade/invalid/', TemplateView.as_view(template_name="bp/project_grade_invalid_secret.html"),
         name="ag_grade_invalid"),
    path('grade/<str:order_id>/success/', AGGradeSuccessView.as_view(), name="ag_grade_success"),
    path('grade/<str:order_id>/<str:secret>/', AGGradeView.as_view(), name="ag_grade"),
]
