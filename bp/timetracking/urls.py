from django.urls import path, include

from .views import \
     TimetrackingOverview, TimetrackingIntervalsDetailView, \
     TimetrackingIntervalsView, TimetrackingIntervalsCreateView

timetracking_intervals_patterns = [
    path('', TimetrackingIntervalsView.as_view(), name="timetracking_intervals"),
    path('new/', TimetrackingIntervalsCreateView.as_view(), name="timetracking_interval_create"),
]

timetracking_interval_content_patterns = [
    path('intervals/<pk>/detail/', TimetrackingIntervalsDetailView.as_view(), name="timetracking_interval_detail"),
    path('intervals/<pk>/edit/', StudentTimetrackingEntryCorrectView.as_view(), name="timetracking_interval_edit"),
]

timetracking_patterns = [
    path('', TimetrackingOverview.as_view(), name="timetracking_tl_start"),
    path('<int:group>/admin/', include(timetracking_intervals_patterns)),
    path('<int:group>/', include(timetracking_interval_content_patterns)),
]
