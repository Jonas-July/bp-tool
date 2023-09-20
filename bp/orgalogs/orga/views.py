import datetime

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse_lazy
from django.views.generic import DetailView, CreateView, TemplateView

from bp.roles import is_orga

from ..models import OrgaLog

# necessary to load the project info tags
from .project_info_tags import *
from ...models import BP, Project


class OrgaLogCreateView(TemplateView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if not is_orga(request.user):
            return HttpResponseForbidden("")
        log = OrgaLog.objects.create(
            bp=BP.get_active(),
            group=Project.objects.get(pk=request.POST['group_id']),
            text=request.POST['text'],
            edited=False
        )
        context = self.get_context_data()
        context['new_orgalog'] = log
        return HttpResponse(log.pk)


class OrgaLogUpdateView(TemplateView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if not is_orga(request.user):
            return HttpResponseForbidden("")
        log = OrgaLog.objects.get(pk=self.kwargs['pk'])
        log.text = request.POST['text']
        log.edited = True
        log.save()
        return HttpResponse("")


class OrgaLogDeleteView(TemplateView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if not is_orga(request.user):
            return HttpResponseForbidden("")
        log = OrgaLog.objects.get(pk=self.kwargs['pk'])
        log.delete()
        return HttpResponse("")
