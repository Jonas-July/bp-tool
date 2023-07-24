from django.urls import path, include

from bp.grading.urls import grading_patterns
from bp.timetracking.urls import timetracking_patterns
from bp.dataimport.urls import import_patterns
from bp.index.urls import index_and_login_patterns
from bp.tllogs.urls import tllog_patterns, tllog_orga_patterns
from bp.orgalogs.urls import orgalog_patterns
from bp.timetracking.views import TimetrackingStatisticsOrgaView

from bp.views import \
    ProjectListView, ProjectUngradedListView, ProjectView, grade_export_view, ProjectImportView, \
    TLView, TLListView, StudentListView, StudentImportView, ProjectEditPitchPoints, ProjectEditDocumentationPoints

app_name = "bp"

urlpatterns = [
    path('', include(index_and_login_patterns)),
    path('projects/', ProjectListView.as_view(), name="project_list"),
    path('projects/timetracking_statistics', TimetrackingStatisticsOrgaView.as_view(), name="timetracking_statistics_orga"),
    path('project/import/', ProjectImportView.as_view(), name="project_import"),
    path('project/export_grades/', grade_export_view, name="project_export_grades"),
    path('project/<pk>/', ProjectView.as_view(), name="project_detail"),
    path('project/<pk>/edit_points/pitch', ProjectEditPitchPoints.as_view(), name="project_edit_pitch_points"),
    path('project/<pk>/edit_points/documentation', ProjectEditDocumentationPoints.as_view(), name="project_edit_documentation_points"),
    path('project/ungraded', ProjectUngradedListView.as_view(), name="project_list_ungraded"),
    path('tl/', TLListView.as_view(), name="tl_list"),
    path('tl/<pk>/', TLView.as_view(), name="tl_detail"),
    path('logs/', include(tllog_orga_patterns)),
    path('orgalogs/', include(orgalog_patterns)),
    path('student/', StudentListView.as_view(), name="student_list"),
    path('student/import/', StudentImportView.as_view(), name="student_import"),
    path('grade/', include(grading_patterns)),
    path('log/', include(tllog_patterns)),
    path('timetracking/', include(timetracking_patterns)),
    path('import/', include(import_patterns))
]
