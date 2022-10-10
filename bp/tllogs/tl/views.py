from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, DetailView, UpdateView, CreateView, DeleteView

from bp.forms import TLLogForm, TLLogUpdateForm
from bp.models import BP, Project, TLLog

from bp.roles import is_tl, is_tl_of_group


class ProjectByRequestMixin:
    def get_project_by_request(self, request):
        return get_object_or_404(Project, nr=self.kwargs.get("group", -1), bp=BP.get_active())


class LogTLOverview(LoginRequiredMixin, TemplateView):
    template_name = "bp/tllogs/tl/log_tl_overview.html"

    def get(self, request, *args, **kwargs):
        if not is_tl(request.user):
            return redirect("bp:index")
        return super().get(request, *args, **kwargs)


class LogTLCreateView(ProjectByRequestMixin, LoginRequiredMixin, CreateView):
    model = TLLog
    form_class = TLLogForm
    template_name = "bp/tllogs/tl/log_tl_create_update.html"

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display projects that belong to a given user"""

        kwargs = super(LogTLCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Log gespeichert")
        return reverse_lazy('bp:log_tl_start')

    def get(self, request, *args, **kwargs):
        project = self.get_project_by_request(request)
        if not is_tl(request.user):
            return redirect("bp:index")
        if not is_tl_of_group(project, request.user):
            messages.add_message(request, messages.WARNING, "Du darfst für diese Gruppe kein Log anlegen")
            return redirect("bp:log_tl_start")
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initials = super().get_initial()

        project = self.get_project_by_request(self.request)

        # Populate hidden form fields
        initials["group"] = project
        initials["bp"] = project.bp
        initials["tl"] = self.request.user.tl

        return initials


def does_log_belong_to_group(group, log):
    return log.group == group

def is_log_of_tl(user, log):
    author = log.tl
    return user.tl == author


class LogTLUpdateView(ProjectByRequestMixin, LoginRequiredMixin, UpdateView):
    model = TLLog
    form_class = TLLogUpdateForm
    template_name = "bp/tllogs/tl/log_tl_create_update.html"

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Log aktualisiert")
        return reverse_lazy('bp:log_tl_start')

    def get(self, request, *args, **kwargs):
        project = self.get_project_by_request(request)
        if not is_tl(request.user):
            return redirect("bp:index")
        if not is_tl_of_group(project, request.user):
            messages.add_message(request, messages.WARNING, "Du darfst für diese Gruppe kein Log ändern")
            return redirect("bp:log_tl_start")
        if not does_log_belong_to_group(project, self.get_object()):
            messages.add_message(request, messages.WARNING, "Ungültiges Log")
            return redirect("bp:log_tl_start")
        if not is_log_of_tl(request.user, self.get_object()):
            messages.add_message(request, messages.WARNING, "Du darfst dieses Log nicht ändern")
            return redirect("bp:log_tl_start")
        return super().get(request, *args, **kwargs)


class LogTLDetailView(ProjectByRequestMixin, LoginRequiredMixin, DetailView):
    model = TLLog
    template_name = "bp/tllogs/tl/log_tl_detail.html"
    context_object_name = "log"

    def get(self, request, *args, **kwargs):
        project = self.get_project_by_request(request)
        if not is_tl(request.user):
            return redirect("bp:index")
        if not is_tl_of_group(project, request.user):
            messages.add_message(request, messages.WARNING, "Du darfst kein Log dieser Gruppe ansehen")
            return redirect("bp:log_tl_start")
        if not does_log_belong_to_group(project, self.get_object()):
            messages.add_message(request, messages.WARNING, "Ungültiges Log")
            return redirect("bp:log_tl_start")
        return super().get(request, *args, **kwargs)

class LogTLDeleteView(ProjectByRequestMixin, LoginRequiredMixin, DeleteView):
    model = TLLog
    template_name = "bp/tllogs/tl/log_tl_delete.html"

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Log gelöscht")
        return reverse_lazy('bp:log_tl_start')

    def get(self, request, *args, **kwargs):
        project = self.get_project_by_request(request)
        if not is_tl(request.user):
            return redirect("bp:index")
        if not is_tl_of_group(project, request.user):
            messages.add_message(request, messages.WARNING, "Du darfst für diese Gruppe kein Log löschen")
            return redirect("bp:log_tl_start")
        if not does_log_belong_to_group(project, self.get_object()):
            messages.add_message(request, messages.WARNING, "Ungültiges Log")
            return redirect("bp:log_tl_start")
        if not is_log_of_tl(request.user, self.get_object()):
            messages.add_message(request, messages.WARNING, "Du darfst dieses Log nicht löschen")
            return redirect("bp:log_tl_start")
        return super().get(request, *args, **kwargs)
