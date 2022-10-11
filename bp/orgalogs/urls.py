from django.urls import path, include

from .orga.views import OrgaLogView, OrgaLogCreateView

orgalog_patterns = [
    path('<group>/new/', OrgaLogCreateView.as_view(), name='orga_log_create'),
    path('<pk>/', OrgaLogView.as_view(), name='orga_log_detail'),
]