from django.shortcuts import get_object_or_404

from bp.models import BP, Project

class ProjectByRequestMixin:
    def get_project_by_request(self, request):
        return get_object_or_404(Project, nr=self.kwargs.get("group", -1), bp=BP.get_active())
