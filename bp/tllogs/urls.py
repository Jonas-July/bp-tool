from django.urls import path

from .api.views import APILogMarkReadView, APILogMarkHandledView, APILogRate
from .orga.views import LogListView, LogAttentionListView, LogUnreadListView, LogReminderView, LogView, \
    LogUnratedListView, NextLog
from .tl.views import LogTLOverview, LogTLCreateView, LogTLUpdateView, LogTLDeleteView, LogTLDetailView

tllog_patterns = [
    path('', LogTLOverview.as_view(), name="log_tl_start"),
    path('<int:group>/new/', LogTLCreateView.as_view(), name="log_tl_create"),
    path('<int:group>/detail/<pk>/', LogTLDetailView.as_view(), name="log_tl_detail"),
    path('<int:group>/edit/<pk>/', LogTLUpdateView.as_view(), name="log_tl_update"),
    path('<int:group>/delete/<pk>/', LogTLDeleteView.as_view(), name="log_tl_delete"),
]

tllog_orga_patterns = [
    path('', LogListView.as_view(), name='log_list'),
    path('attention/', LogAttentionListView.as_view(), name='log_list_attention'),
    path('unread/', LogUnreadListView.as_view(), name='log_list_unread'),
    path('unrated/', LogUnratedListView.as_view(), name='log_list_unrated'),
    path('remind/<int:period>', LogReminderView.as_view(), name='log_remind'),
    path('<pk>/', LogView.as_view(), name='log_detail'),
    path('<pk>/read/', APILogMarkReadView.as_view(), name='log_api_mark_read'),
    path('<pk>/handled/', APILogMarkHandledView.as_view(), name='log_api_mark_handled'),
    path('<pk>/rate/', APILogRate.as_view(), name='log_api_rate'),
    path('<pk>/next_log', NextLog.as_view(), name='next_log'),
]