from django.urls import path, include

from bp.views import OrgaLogView

orgalog_patterns = [
    path('<pk>/', OrgaLogView.as_view(), name='orga_log_detail'),
]