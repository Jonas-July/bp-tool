from django.urls import path, include

from .views import \
     TimetrackingOverview, TimetrackingProjectOverview, TimetrackingIntervalsDetailView, \
     TimetrackingIntervalsView, TimetrackingIntervalsCreateView, \
     TLTimetrackingEntryCorrectView, StudentTimetrackingEntryCorrectView, ApiTimetrackingEntryAddHours, \
     TimetrackingMembersDetailView

timetracking_intervals_patterns = [
    path('', TimetrackingIntervalsView.as_view(), name="timetracking_intervals"),
    path('new/', TimetrackingIntervalsCreateView.as_view(), name="timetracking_interval_create"),
]

timetracking_interval_content_patterns = [
    path('overview', TimetrackingProjectOverview.as_view(), name="timetracking_project_overview"),
    path('intervals/<pk>/detail/', TimetrackingIntervalsDetailView.as_view(), name="timetracking_interval_detail"),
    path('intervals/<pk>/correct', TLTimetrackingEntryCorrectView.as_view(), name="timetracking_interval_tl_correct"),
    path('intervals/<pk>/edit/', StudentTimetrackingEntryCorrectView.as_view(), name="timetracking_interval_edit"),
    path('intervals/<pk>/add_hours/', ApiTimetrackingEntryAddHours.as_view(), name="timetracking_api_add_hours"),
    path('members/<pk>/detail/', TimetrackingMembersDetailView.as_view(), name="timetracking_members_detail"),
]

timetracking_patterns = [
    path('', TimetrackingOverview.as_view(), name="timetracking_tl_start"),
    path('<int:group>/admin/', include(timetracking_intervals_patterns)),
    path('<int:group>/', include(timetracking_interval_content_patterns)),
]
