from django.urls import path, include

from bp.grading.urls import grading_patterns
from bp.timetracking.urls import timetracking_patterns
from bp.index.urls import index_and_login_patterns

from bp.views import \
    ProjectListView, ProjectUngradedListView, ProjectView, grade_export_view, ProjectImportView, \
    TLView, TLListView, StudentListView, StudentImportView, \
    LogListView, LogAttentionListView, LogUnreadListView, LogView, LogReminderView, \
    APILogMarkReadView, APILogMarkHandledView, APILogMarkGoodView, APILogMarkBadView, \
    LogTLOverview, LogTLCreateView, LogTLUpdateView, LogTLDeleteView, LogTLDetailView, \
    OrgaLogView \

app_name = "bp"

urlpatterns = [
    path('', include(index_and_login_patterns)),
    path('project/', ProjectListView.as_view(), name="project_list"),
    path('project/import/', ProjectImportView.as_view(), name="project_import"),
    path('project/export_grades/', grade_export_view, name="project_export_grades"),
    path('project/<pk>/', ProjectView.as_view(), name="project_detail"),
    path('project/ungraded', ProjectUngradedListView.as_view(), name="project_list_ungraded"),
    path('tl/', TLListView.as_view(), name="tl_list"),
    path('tl/<pk>/', TLView.as_view(), name="tl_detail"),
    path('logs/', LogListView.as_view(), name='log_list'),
    path('logs/attention/', LogAttentionListView.as_view(), name='log_list_attention'),
    path('logs/unread/', LogUnreadListView.as_view(), name='log_list_unread'),
    path('logs/remind/', LogReminderView.as_view(), name='log_remind'),
    path('logs/<pk>/', LogView.as_view(), name='log_detail'),
    path('logs/<pk>/read/', APILogMarkReadView.as_view(), name='log_api_mark_read'),
    path('logs/<pk>/handled/', APILogMarkHandledView.as_view(), name='log_api_mark_handled'),
    path('logs/<pk>/good/', APILogMarkGoodView.as_view(), name='log_api_mark_good'),
    path('logs/<pk>/bad/', APILogMarkBadView.as_view(), name='log_api_mark_bad'),
    path('orgalogs/<pk>/', OrgaLogView.as_view(), name='orga_log_detail'),
    path('student/', StudentListView.as_view(), name="student_list"),
    path('student/import/', StudentImportView.as_view(), name="student_import"),
    path('grade/', include(grading_patterns)),
    path('log/', LogTLOverview.as_view(), name="log_tl_start"),
    path('log/<int:group>/new/', LogTLCreateView.as_view(), name="log_tl_create"),
    path('log/<int:group>/detail/<pk>/', LogTLDetailView.as_view(), name="log_tl_detail"),
    path('log/<int:group>/edit/<pk>/', LogTLUpdateView.as_view(), name="log_tl_update"),
    path('log/<int:group>/delete/<pk>/', LogTLDeleteView.as_view(), name="log_tl_delete"),
    path('timetracking/', include(timetracking_patterns)),
]
