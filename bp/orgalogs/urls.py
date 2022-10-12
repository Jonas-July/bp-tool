from django.urls import path, include

from .orga.views import OrgaLogView

orgalog_patterns = [
    path('<pk>/', OrgaLogView.as_view(), name='orga_log_detail'),
]