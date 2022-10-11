from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import DetailView

from bp.models import OrgaLog


class OrgaLogView(PermissionRequiredMixin, DetailView):
    model = OrgaLog
    template_name = "bp/orgalog.html"
    context_object_name = "log"
    permission_required = "bp.view_orgalog"
