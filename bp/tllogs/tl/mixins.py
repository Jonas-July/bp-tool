from django.shortcuts import get_object_or_404

from bp.models import BP, Project
from bp.roles import get_bp_of_user

class ProjectByRequestMixin:
    def get_project_by_request(self, request):
        return get_object_or_404(Project, nr=self.kwargs.get("group", -1), bp=get_bp_of_user(request.user))
