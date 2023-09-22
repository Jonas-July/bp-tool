from django.urls import path, include

from .orga.views import OrgaLogCreateView, OrgaLogUpdateView, OrgaLogDeleteView

orgalog_patterns = [
    path('<group>/new/', OrgaLogCreateView.as_view(), name='orga_log_create'),
    path('<pk>/update/', OrgaLogUpdateView.as_view(), name='orga_log_update'),
    path('<pk>/delete/', OrgaLogDeleteView.as_view(), name='orga_log_delete'),
]