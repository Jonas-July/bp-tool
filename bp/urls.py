from django.urls import path
from django.views.generic import TemplateView

from bp.views import IndexView, ProjectListView, ProjectView, TLView, TLListView, AGGradeView, AGGradeSuccessView, \
    ProjectImportView, StudentListView, StudentImportView, grade_export_view, LogTLOverview, LogTLCreateView, \
    LogTLUpdateView, LogTLDeleteView, LogListView, LogView, LogAttentionListView, APILogMarkReadView, \
    APILogMarkHandledView, APILogMarkGoodView, APILogMarkBadView, LogReminderView, LogTLDetailView, LoginView

app_name = "bp"

urlpatterns = [
    path('', IndexView.as_view(), name="index"),
    path('project/', ProjectListView.as_view(), name="project_list"),
    path('project/import/', ProjectImportView.as_view(), name="project_import"),
    path('project/export_grades/', grade_export_view, name="project_export_grades"),
    path('project/<pk>/', ProjectView.as_view(), name="project_detail"),
    path('tl/', TLListView.as_view(), name="tl_list"),
    path('tl/<pk>/', TLView.as_view(), name="tl_detail"),
    path('logs/', LogListView.as_view(), name='log_list'),
    path('logs/attention/', LogAttentionListView.as_view(), name='log_list_attention'),
    path('logs/remind/', LogReminderView.as_view(), name='log_remind'),
    path('logs/<pk>/', LogView.as_view(), name='log_detail'),
    path('logs/<pk>/read/', APILogMarkReadView.as_view(), name='log_api_mark_read'),
    path('logs/<pk>/handled/', APILogMarkHandledView.as_view(), name='log_api_mark_handled'),
    path('logs/<pk>/good/', APILogMarkGoodView.as_view(), name='log_api_mark_good'),
    path('logs/<pk>/bad/', APILogMarkBadView.as_view(), name='log_api_mark_bad'),
    path('student/', StudentListView.as_view(), name="student_list"),
    path('student/import/', StudentImportView.as_view(), name="student_import"),
    path('grade/invalid/', TemplateView.as_view(template_name="bp/project_grade_invalid_secret.html"),
         name="ag_grade_invalid"),
    path('grade/<str:order_id>/success/', AGGradeSuccessView.as_view(), name="ag_grade_success"),
    path('grade/<str:order_id>/<str:secret>/', AGGradeView.as_view(), name="ag_grade"),
    path('log/', LogTLOverview.as_view(), name="log_tl_start"),
    path('log/<int:group>/new/', LogTLCreateView.as_view(), name="log_tl_create"),
    path('log/<int:group>/detail/<pk>/', LogTLDetailView.as_view(), name="log_tl_detail"),
    path('log/<int:group>/edit/<pk>/', LogTLUpdateView.as_view(), name="log_tl_update"),
    path('log/<int:group>/delete/<pk>/', LogTLDeleteView.as_view(), name="log_tl_delete"),
    path('login/', LoginView.as_view(), name="login"),
]
