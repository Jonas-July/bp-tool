from django.urls import path, include

from bp.views import APILogMarkReadView, APILogMarkHandledView, APILogMarkGoodView, APILogMarkBadView
from .orga.views import LogListView, LogAttentionListView, LogUnreadListView, LogReminderView, LogView
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
    path('remind/', LogReminderView.as_view(), name='log_remind'),
    path('<pk>/', LogView.as_view(), name='log_detail'),
    path('<pk>/read/', APILogMarkReadView.as_view(), name='log_api_mark_read'),
    path('<pk>/handled/', APILogMarkHandledView.as_view(), name='log_api_mark_handled'),
    path('<pk>/good/', APILogMarkGoodView.as_view(), name='log_api_mark_good'),
    path('<pk>/bad/', APILogMarkBadView.as_view(), name='log_api_mark_bad'),
]