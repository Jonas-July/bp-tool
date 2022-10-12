from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, CreateView

from bp.roles import is_orga

from ..models import OrgaLog
from .forms import OrgaLogForm
from .mixins import ProjectByRequestMixin

# necessary to load the project info tags
from .project_info_tags import *

class OrgaLogView(PermissionRequiredMixin, DetailView):
    model = OrgaLog
    template_name = "bp/orgalogs/orga/orgalog.html"
    context_object_name = "log"
    permission_required = "bp.view_orgalog"


class OrgaLogCreateView(PermissionRequiredMixin, ProjectByRequestMixin, CreateView):
    model = OrgaLog
    form_class = OrgaLogForm
    template_name = "bp/orgalogs/orga/orgalog_create.html"
    permission_required = "bp.add_orgalog"

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Orgalog gespeichert")
        return reverse_lazy('bp:project_detail', kwargs={'pk' : self.get_project_by_request(self.request).pk})

    def get(self, request, *args, **kwargs):
        if not is_orga(request.user):
            return redirect("bp:index")
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initials = super().get_initial()

        project = self.get_project_by_request(self.request)

        # Populate hidden form fields
        initials["group"] = project
        initials["bp"] = project.bp

        return initials

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = self.get_project_by_request(self.request)
        return context
