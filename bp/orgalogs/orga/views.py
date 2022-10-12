from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import DetailView

from bp.models import OrgaLog

# necessary to load the project info tags
from .project_info_tags import *

class OrgaLogView(PermissionRequiredMixin, DetailView):
    model = OrgaLog
    template_name = "bp/orgalogs/orga/orgalog.html"
    context_object_name = "log"
    permission_required = "bp.view_orgalog"
