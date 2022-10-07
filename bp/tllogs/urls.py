from django.urls import path, include

from .tl.views import LogTLOverview, LogTLCreateView, LogTLUpdateView, LogTLDeleteView, LogTLDetailView

tllog_patterns = [
    path('', LogTLOverview.as_view(), name="log_tl_start"),
    path('<int:group>/new/', LogTLCreateView.as_view(), name="log_tl_create"),
    path('<int:group>/detail/<pk>/', LogTLDetailView.as_view(), name="log_tl_detail"),
    path('<int:group>/edit/<pk>/', LogTLUpdateView.as_view(), name="log_tl_update"),
    path('<int:group>/delete/<pk>/', LogTLDeleteView.as_view(), name="log_tl_delete"),
]