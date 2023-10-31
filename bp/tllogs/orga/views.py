from functools import reduce

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, FormView

from .forms import LogReminderForm
from bp.models import Project, TLLog
from bp.views import FilterByActiveBPMixin

# necessary to load the custom tags
from .templatetags import project_info_tags, project_overview_list_tags


class LogListView(PermissionRequiredMixin, FilterByActiveBPMixin, ListView):
    model = TLLog
    template_name = "bp/tllogs/orga/log_overview.html"
    context_object_name = "logs"
    permission_required = "bp.view_tllog"
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related('group', 'tl').prefetch_related("current_problems")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Logs"
        return context


class LogAttentionListView(LogListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Logs (Aufmerksamkeit nötig)"
        return context

    def get_queryset(self):
        return super().get_queryset().filter(requires_attention=True)


class LogUnreadListView(LogListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Logs (Ungelesen)"
        return context

    def get_queryset(self):
        return super().get_queryset().filter(read=False)


class LogUnratedListView(LogListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Logs (Unbewertet)"
        return context

    def get_queryset(self):
        return super().get_queryset().filter(rating=None)


class LogView(PermissionRequiredMixin, DetailView):
    model = TLLog
    template_name = "bp/tllogs/orga/log.html"
    context_object_name = "log"
    permission_required = "bp.view_tllog"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        log = self.get_object()
        rating = log.rating

        if rating:
            context["rating"] = rating
        else:
            context["rating"] = 0

        return context


class LogReminderView(PermissionRequiredMixin, FormView):
    template_name = "bp/tllogs/orga/log_reminder.html"
    form_class = LogReminderForm
    permission_required = "bp.view_tllog"
    success_url = reverse_lazy("bp:log_list")

    def get_initial(self):
        initial = super().get_initial()
        projects_to_remind = [p for p in Project.no_log_or_reminder_since(self.kwargs.get("period"))]
        tl_choices = {}
        for p in projects_to_remind:
            if p.tl in tl_choices:
                tl_choices.get(p.tl).append(p)
            else:
                tl_choices[p.tl] = [p]
        initial['tl_choices'] = [([tl.pk, [p.pk for p in projects], self.kwargs.get("period")],
                                  f"{tl.name}: {', '.join([p.short_title_else_title for p in projects])}")
                                 for tl, projects in tl_choices.items()]
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['log_period'] = self.kwargs.get("period")
        return context

    def form_valid(self, form):
        message = form.send_reminders()
        messages.add_message(self.request, messages.SUCCESS, message)
        return super().form_valid(form)


class NextLog(DetailView):
    model = TLLog

    def get(self, request, *args, **kwargs):

        current_log = self. get_object()
        unread_logs = list(TLLog.get_active().filter(Q(read=False) | Q(pk=current_log.pk)).order_by('pk'))
        if len(unread_logs) <= 1:
            messages.add_message(request, messages.WARNING, "Es gibt keine weiteren ungelesenen Logs.")
            return redirect("bp:log_detail", current_log.pk)
        else:
            try:
                next_log = unread_logs[unread_logs.index(current_log) + 1]
            except IndexError:
                next_log = unread_logs[0]
        return redirect("bp:log_detail", next_log.pk)
