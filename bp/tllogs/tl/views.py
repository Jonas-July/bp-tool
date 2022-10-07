from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, DetailView, UpdateView, CreateView, DeleteView


from bp.forms import TLLogForm, TLLogUpdateForm
from bp.models import BP, Project, TLLog


class LogTLOverview(LoginRequiredMixin, TemplateView):
    template_name = "bp/log_tl_overview.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return redirect("bp:index")
        return super().get(request, *args, **kwargs)


class LogTLCreateView(LoginRequiredMixin, CreateView):
    model = TLLog
    form_class = TLLogForm
    template_name = "bp/log_tl_create_update.html"

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display projects that belong to a given user"""

        kwargs = super(LogTLCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Log gespeichert")
        return reverse_lazy('bp:log_tl_start')

    def get_project_by_request(self, request):
        return get_object_or_404(Project, nr=self.kwargs.get("group", -1), bp=BP.get_active())

    def get(self, request, *args, **kwargs):
        project = self.get_project_by_request(request)
        if self.request.user.tl != project.tl:
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

class OnlyOwnLogsMixin:
    def get_object(self, queryset=None):
        log = super().get_object(queryset)
        if log.tl != self.request.user.tl:
            raise Http404("Zugriff verweigert")
        return log


class LogTLUpdateView(LoginRequiredMixin, OnlyOwnLogsMixin, UpdateView):
    model = TLLog
    form_class = TLLogUpdateForm
    template_name = "bp/log_tl_create_update.html"

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Log aktualisiert")
        return reverse_lazy('bp:log_tl_start')


class LogTLDetailView(LoginRequiredMixin, OnlyOwnLogsMixin, DetailView):
    model = TLLog
    template_name = "bp/log_tl_detail.html"
    context_object_name = "log"


class LogTLDeleteView(LoginRequiredMixin, DeleteView):
    model = TLLog
    template_name = "bp/log_tl_delete.html"

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Log gelöscht")
        return reverse_lazy('bp:log_tl_start')
