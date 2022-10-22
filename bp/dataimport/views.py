from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from bp.roles import is_orga

class DataImportView(LoginRequiredMixin, TemplateView):
    template_name = "bp/dataimport/import.html"

    def get(self, request, *args, **kwargs):
        if not is_orga(request.user):
            return redirect("bp:index")
        return super().get(request, *args, **kwargs)