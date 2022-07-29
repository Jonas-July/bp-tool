from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import formats
from django.views.generic import TemplateView, DetailView, CreateView, FormView, UpdateView, DeleteView

from bp.models import BP, Project, Student

from .forms import TimeIntervalForm
from .models import TimeInterval, TimeTrackingEntry, TimeSpentCategory


class ProjectByRequestMixin:
    def get_project_by_request(self, request):
        return get_object_or_404(Project, nr=self.kwargs.get("group", -1), bp=BP.get_active())

class ProjectByGroupMixin(ProjectByRequestMixin):
    def get_object(self, queryset=None):
        return self.get_project_by_request(self.request)

def is_tl(user):
    return hasattr(user, 'tl')
def is_student(user):
    return hasattr(user, 'student')

def is_tl_or_student(user):
    return is_tl(user) or is_student(user)

def is_tl_of_group(group, user):
    return user.tl == group.tl

def is_neither_tl_nor_student_of_group(group, user):
    if is_tl(user) and is_tl_of_group(group, user):
        return False
    if is_student(user) and user.student in group.student_set.all():
        return False
    return True

class OnlyOwnTimeIntervalsMixin:
    def get_object(self, queryset=None):
        timeinterval = super().get_object(queryset)
        if is_neither_tl_nor_student_of_group(timeinterval.group, self.request.user):
            raise Http404("Zugriff verweigert")
        return timeinterval

class TimeTable:
    def __init__(self, rows, columns, entry_function):
        self.rows = rows
        self.columns = columns
        self.create_entry = entry_function

    def get_table(self):
        return [  ["",  *[col for col in self.columns]], # header
                *([row, *[self.create_entry(col, row) for col in self.columns]] for row in self.rows)
               ]

class TimetrackingOverview(LoginRequiredMixin, TemplateView):
    template_name = "bp/timetracking/timetracking_overview.html"

    def get(self, request, *args, **kwargs):
        if not is_tl_or_student(request.user):
            return redirect("bp:index")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        def hours_of_student_in_interval(student, interval):
            hours = interval.timetrackingentry_set.filter(student=student).aggregate(hours=Coalesce(Sum('hours'), Decimal(0)))['hours']
            return round(hours, 2)
        context = super().get_context_data(**kwargs)
        projects = self.request.user.tl.project_set.all() if is_tl(self.request.user) \
                   else Project.objects.filter(pk=self.request.user.student.project.pk)
        context["projects"] = projects.prefetch_related('student_set', 'timeinterval_set')
        context["timetables"] = \
            [(project,
              project.total_hours,
              TimeTable(project.get_past_and_current_intervals, project.student_set.all(), hours_of_student_in_interval).get_table(),
             ) for project in context["projects"]]
        return context

class TimetrackingIntervalsView(ProjectByGroupMixin, PermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "bp/timetracking/timetracking_intervals.html"
    permission_required = "bp.view_timeinterval"

    def get(self, request, *args, **kwargs):
        if not is_tl(request.user):
            return redirect("bp:index")
        if not is_tl_of_group(self.get_object(), request.user):
            messages.add_message(request, messages.WARNING, "Du darfst für diese Gruppe keine Intervalle anlegen")
            return redirect("bp:timetracking_tl_start")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_object()
        context["intervals"] = context["project"].timeinterval_set.all().order_by("-start")
        return context

class TimetrackingIntervalsCreateView(ProjectByGroupMixin, PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = TimeInterval
    form_class = TimeIntervalForm
    template_name = "bp/timetracking_interval_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_object()
        return context

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display projects that belong to a given user"""

        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Intervall gespeichert")
        return reverse_lazy('bp:timetracking_intervals', kwargs={'group' : self.get_project_by_request(self.request).nr})

    def get(self, request, *args, **kwargs):
        project = self.get_project_by_request(request)
        if not is_tl(request.user):
            return redirect("bp:index")
        if not is_tl_of_group(project, request.user):
            messages.add_message(request, messages.WARNING, "Du darfst für diese Gruppe keine Intervalle anlegen")
            return redirect("bp:timetracking_tl_start")
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initials = super().get_initial()

        project = self.get_project_by_request(self.request)

        # Populate hidden form fields
        initials["group"] = project

        return initials

class TimetrackingIntervalsDetailView(ProjectByRequestMixin, OnlyOwnTimeIntervalsMixin, LoginRequiredMixin, DetailView):
    model = TimeInterval
    template_name = "bp/timetracking/timetracking_interval_detail.html"
    context_object_name = "timeinterval"

    def get(self, request, *args, **kwargs):
        project = self.get_project_by_request(request)
        if is_neither_tl_nor_student_of_group(project, self.request.user):
            messages.add_message(request, messages.WARNING, "Du darfst nur die Zeiten deiner eigenen Gruppe(n) sehen")
            return redirect("bp:timetracking_tl_start")
        if not self.get_object() in project.get_past_and_current_intervals:
            messages.add_message(request, messages.WARNING, "Ungültiges Intervall")
            return redirect("bp:timetracking_tl_start")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project = self.get_project_by_request(self.request)
        interval = self.get_object()
        categories = TimeSpentCategory.objects.all()
        def hours_of_student_in_category(s, cat):
            hours_cat = Coalesce(Sum('hours'), Decimal(0))
            hours = interval.timetrackingentry_set.filter(category=cat, student=s).aggregate(hours=hours_cat)['hours']
            return round(hours, 2)

        context["group"] = project
        all_students = list(project.student_set.all())
        context["timetable"] = TimeTable(categories, all_students, hours_of_student_in_category).get_table()
        if is_student(self.request.user):
            context["editing_student"] = self.request.user.student
        context["is_student_editable"] = interval.is_editable_by_students()

        return context

