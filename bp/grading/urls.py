from django.urls import path, include
from django.views.generic import TemplateView

from .ag.views import AGGradeView, AGGradeSuccessView, AGGradeEarlyView

aggrade_patterns = [
    path('invalid/', TemplateView.as_view(template_name="bp/project_grade_invalid_secret.html"),
         name="ag_grade_invalid"),
    path('<str:order_id>/early/', AGGradeEarlyView.as_view(), name="ag_grade_too_early"),
    path('<str:order_id>/success/', AGGradeSuccessView.as_view(), name="ag_grade_success"),
    path('<str:order_id>/<str:secret>/', AGGradeView.as_view(), name="ag_grade"),
]

grading_patterns = [
    path('', include(aggrade_patterns))
]