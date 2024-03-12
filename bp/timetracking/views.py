from decimal import Decimal, InvalidOperation
import json

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
from bp.roles import is_tl, is_student, is_orga, is_tl_or_student, is_tl_of_group, is_student_of_group, \
    is_neither_tl_nor_student_of_group
from bp.roles import get_bp_of_user

from .forms import TimeIntervalForm, TimeIntervalGenerationForm, TimeIntervalUpdateForm, \
    TLTimeIntervalEntryCorrectionForm
from .models import TimeInterval, TimeTrackingEntry, TimeSpentCategory

# necessary to load the project info tags
from . import project_info_tags


class ProjectByRequestMixin:
    def get_project_by_request(self, request):
        return get_object_or_404(Project, nr=self.kwargs.get("group", -1), bp=get_bp_of_user(request.user))


class TimeIntervalByRequestMixin:
    def get_interval_by_request(self, request):
        return get_object_or_404(TimeInterval, pk=self.kwargs.get("pk", -1))


class ProjectByGroupMixin(ProjectByRequestMixin):
    def get_object(self, queryset=None):
        return self.get_project_by_request(self.request)


class OnlyOwnTimeIntervalsMixin:
    def get_object(self, queryset=None):
        timeinterval = super().get_object(queryset)
        if is_neither_tl_nor_student_of_group(timeinterval.group, self.request.user):
            raise Http404("Zugriff verweigert")
        return timeinterval


class OnlyOwnEmptyTimeIntervalsMixin(OnlyOwnTimeIntervalsMixin):
    def get_object(self, queryset=None):
        timeinterval = super().get_object(queryset)
        if timeinterval.timetrackingentry_set.all():
            raise Http404("Intervall mit Einträgen kann nicht gelöscht werden")
        return timeinterval


class TimeTable:
    def __init__(self, rows, columns, entry_function):
        self.rows = rows
        self.columns = columns
        self.create_entry = entry_function

    def get_table(self):
        return [[(None, None, ""), *[(None, None, col) for col in self.columns]],  # header
                *([(None, None, row), *[(col, row, self.create_entry(col, row)) for col in self.columns]] for row in
                  self.rows)
                ]


# needed for timetracking graphs
class Chart:
    def __init__(self, datapoints):
        self.datapoints = datapoints

    def get_chart_data(self):
        return json.dumps(self.datapoints)

    def sort(self):
        self.datapoints = sorted(self.datapoints, key=lambda d: d['y'])

    def single_bar_highlighted(self, bar_name):
        colors = ['#FFA000' if point.get('x') == str(bar_name) else '#1F9BCF' for point in self.datapoints]
        return f'{colors}'


# needed for timetracking graphs of time spent - group comparison
class HoursPerGroupData:
    def __init__(self, category_name, data, colors, identifier):
        self.category_name = category_name
        self.data = data
        self.colors = colors
        self.chart_id = identifier


class TimetrackingOverview(LoginRequiredMixin, TemplateView):
    template_name = "bp/timetracking/timetracking_overview.html"

    def get(self, request, *args, **kwargs):
        if not is_tl_or_student(request.user):
            return redirect("bp:index")
        if is_student(request.user):
            return redirect("bp:timetracking_project_overview", group=request.user.student.project.nr)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        def hours_of_student_in_interval(student, interval):
            hours = \
                interval.timetrackingentry_set.filter(student=student).aggregate(
                    hours=Coalesce(Sum('hours'), Decimal(0)))[
                    'hours']
            return round(hours, 2)

        context = super().get_context_data(**kwargs)
        projects = self.request.user.tl.project_set.all()
        context["projects"] = projects.prefetch_related('student_set', 'timeinterval_set')
        context["timetables"] = \
            [(project, project.total_hours,) for project in context["projects"]]
        return context


# needed for timetracking graphs of time spent - group comparison
def get_hours_per_group(category=None):
    chart = Chart([
        {
            'x': f'{proj.nr}',
            'y': f'{proj.total_hours_of_category(category) if category else proj.total_hours}'
        } for proj in Project.get_active()
    ])

    chart.sort()
    return chart


class TimetrackingProjectOverview(ProjectByGroupMixin, LoginRequiredMixin, TemplateView):
    template_name = "bp/timetracking/timetracking_project_overview.html"

    def get(self, request, *args, **kwargs):
        if is_orga(request.user):
            return super().get(request, *args, **kwargs)
        if not is_tl_or_student(request.user):
            return redirect("bp:index")
        if is_neither_tl_nor_student_of_group(self.get_object(), request.user):
            messages.add_message(request, messages.WARNING, "Du darfst nur die Zeiten deiner eigenen Gruppe(n) sehen")
            return redirect("bp:timetracking_tl_start")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        def hours_of_student_in_interval(student, interval):
            hours = \
                interval.timetrackingentry_set.filter(student=student).aggregate(
                    hours=Coalesce(Sum('hours'), Decimal(0)))[
                    'hours']
            return round(hours, 2)

        context = super().get_context_data(**kwargs)
        project = self.get_object()
        context["project"] = project
        context["total_hours"] = project.total_hours
        students = project.student_set.all()
        context["timetable"] = TimeTable(project.get_past_and_current_intervals, students,
                                         hours_of_student_in_interval).get_table()
        context["students"] = students

        return context


class TimetrackingIntervalsView(ProjectByGroupMixin, LoginRequiredMixin, TemplateView):
    template_name = "bp/timetracking/timetracking_intervals.html"

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


class TimetrackingIntervalsCreateView(ProjectByGroupMixin, LoginRequiredMixin, CreateView):
    model = TimeInterval
    form_class = TimeIntervalForm
    template_name = "bp/timetracking/timetracking_interval_create.html"

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
        return reverse_lazy('bp:timetracking_intervals', kwargs={'group': self.get_project_by_request(self.request).nr})

    def get(self, request, *args, **kwargs):
        project = self.get_project_by_request(request)
        if not is_tl(request.user):
            return redirect("bp:index")
        if not is_tl_of_group(project, request.user):
            messages.add_message(request, messages.WARNING, "Du darfst für diese Gruppe keine Intervalle anlegen.")
            return redirect("bp:timetracking_tl_start")
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initials = super().get_initial()

        project = self.get_project_by_request(self.request)

        # Populate hidden form fields
        initials["group"] = project

        return initials


class TimetrackingIntervalsGenerationView(ProjectByRequestMixin, LoginRequiredMixin, FormView):
    form_class = TimeIntervalGenerationForm
    template_name = "bp/timetracking/timetracking_interval_generate.html"
    permission_required = "bp.add_timeinterval"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project_by_request(self.request)
        return context

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display projects that belong to a given user"""

        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        redirect = super().form_valid(form)
        form.save()
        return redirect

    def get_success_url(self):
        return reverse_lazy('bp:timetracking_intervals', kwargs={'group': self.get_project_by_request(self.request).nr})

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
        initials["interval_length"] = 7

        return initials


class TimetrackingIntervalUpdateView(ProjectByRequestMixin, LoginRequiredMixin, OnlyOwnTimeIntervalsMixin, UpdateView):
    model = TimeInterval
    form_class = TimeIntervalUpdateForm
    template_name = "bp/timetracking/timetracking_interval_create_update.html"
    context_object_name = "timeinterval"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project_by_request(self.request)
        return context

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Intervall aktualisiert")
        return reverse_lazy('bp:timetracking_intervals', kwargs={'group': self.get_project_by_request(self.request).nr})


class TimetrackingIntervalDeleteView(ProjectByRequestMixin, OnlyOwnEmptyTimeIntervalsMixin, LoginRequiredMixin,
                                     DeleteView):
    model = TimeInterval
    template_name = "bp/timetracking/timetracking_interval_delete.html"

    def get(self, request, *args, **kwargs):
        project = self.get_project_by_request(request)
        if not is_tl(request.user):
            return redirect("bp:index")
        if not is_tl_of_group(project, request.user):
            messages.add_message(request, messages.WARNING, "Du darfst für diese Gruppe keine Intervalle bearbeiten.")
            return redirect("bp:timetracking_tl_start")
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Intervall gelöscht")
        return reverse_lazy('bp:timetracking_intervals', kwargs={'group': self.get_project_by_request(self.request).nr})


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
        context["student_summaries"] = [sum((hours_of_student_in_category(s, cat) for cat in categories)) for s in
                                        all_students]
        if is_student(self.request.user):
            context["editing_student"] = self.request.user.student
        context["is_student_editable"] = interval.is_editable_by_students()

        return context


class TimetrackingEntryCreateView(ProjectByRequestMixin, TimeIntervalByRequestMixin, LoginRequiredMixin, CreateView):

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Eintrag gespeichert")
        return reverse_lazy('bp:timetracking_interval_detail',
                            kwargs={'group': self.get_project_by_request(self.request).nr,
                                    'pk': self.get_interval_by_request(self.request).pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_project_by_request(self.request)
        context["group"] = group
        context["timeinterval"] = self.get_interval_by_request(self.request)
        return context

    def get_initial(self):
        initials = super().get_initial()

        # Populate hidden form fields
        initials["interval"] = self.get_interval_by_request(self.request)

        return initials


class TLTimetrackingEntryCorrectView(TimetrackingEntryCreateView, LoginRequiredMixin, CreateView):
    model = TimeTrackingEntry
    form_class = TLTimeIntervalEntryCorrectionForm
    template_name = "bp/timetracking/timetracking_entry_correct.html"

    def get_form_kwargs(self):
        """ Passes the interval object to the form class.
         This is necessary to only display students that belong to the group"""

        kwargs = super().get_form_kwargs()
        kwargs['interval'] = self.get_interval_by_request(self.request)
        return kwargs

    def get(self, request, *args, **kwargs):
        project = self.get_project_by_request(request)
        interval = self.get_interval_by_request(request)
        if not is_tl(request.user):
            messages.add_message(request, messages.WARNING, "Ungültige Aktion")
            return redirect("bp:timetracking_tl_start")
        if not is_tl_of_group(project, request.user):
            messages.add_message(request, messages.WARNING, "Ungültige Gruppe")
            return redirect("bp:timetracking_tl_start")
        if not interval in project.get_past_and_current_intervals:
            messages.add_message(request, messages.WARNING, "Ungültiges Intervall")
            return redirect("bp:timetracking_tl_start")
        if interval.is_editable_by_students():
            messages.add_message(request, messages.WARNING,
                                 f"{interval.name} darf von den Teammitgliedern bearbeitet werden. Intervall ist nicht archiviert.")
            return redirect("bp:timetracking_interval_detail", group=project.nr, pk=interval.pk)
        return super().get(request, *args, **kwargs)


class ApiTimetrackingEntryUpdateHours(ProjectByRequestMixin, TimeIntervalByRequestMixin, LoginRequiredMixin, TemplateView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if not is_student(request.user):
            return HttpResponseForbidden("")
        project = self.get_project_by_request(request)
        if not is_student_of_group(project, request.user):
            return HttpResponseForbidden("")
        timeinterval = self.get_interval_by_request(request)
        if not timeinterval in project.get_past_and_current_intervals:
            messages.add_message(request, messages.WARNING, f"Ungültiges Intervall")
            return HttpResponseForbidden("")
        if not timeinterval.is_editable_by_students():
            messages.add_message(request, messages.WARNING,
                                 f"{timeinterval.name} darf nicht mehr bearbeitet werden. Wende dich an die Orga für weitere Infos.")
            return HttpResponseForbidden("")
        category_name, hours = request.POST['category'], request.POST['hours']
        category = TimeSpentCategory.objects.filter(name=category_name).first()
        if not category:
            return HttpResponseForbidden("")
        hours = Decimal(hours)
        if hours < 0:
            return HttpResponseForbidden("")

        obj, created = TimeTrackingEntry.objects.get_or_create(student=self.request.user.student,
                                                               interval=timeinterval,
                                                               category=category,
                                                               defaults={'hours': 0})
        try:
            obj.hours = hours
            obj.save()
        except InvalidOperation:
            return HttpResponseForbidden("")
        obj.refresh_from_db()
        return HttpResponse(formats.localize(obj.hours, use_l10n=True))


class TimetrackingMembersDetailView(ProjectByRequestMixin, LoginRequiredMixin, DetailView):
    model = Student
    template_name = "bp/timetracking/timetracking_member_detail.html"
    context_object_name = "member"

    def get(self, request, *args, **kwargs):
        project = self.get_project_by_request(request)
        if is_neither_tl_nor_student_of_group(project, self.request.user):
            messages.add_message(request, messages.WARNING, "Du darfst nur die Zeiten deiner eigenen Gruppe(n) sehen")
            return redirect("bp:timetracking_tl_start")
        if not self.get_object() in project.student_set.all():
            messages.add_message(request, messages.WARNING, "Ungültiges Teammitglied")
            return redirect("bp:timetracking_tl_start")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project = self.get_project_by_request(self.request)
        member = self.get_object()
        categories = TimeSpentCategory.objects.all()

        def hours_spent_in_category_per_interval(cat, itv):
            hours_cat = Coalesce(Sum('hours'), Decimal(0))
            hours = member.timetrackingentry_set.filter(category=cat, interval=itv).aggregate(hours=hours_cat)['hours']
            return round(hours, 2)

        context["group"] = project
        all_intervals = list(project.get_past_and_current_intervals)
        context["timetable"] = TimeTable(all_intervals, categories, hours_spent_in_category_per_interval).get_table()
        context["categories"] = categories
        context["intervals"] = all_intervals
        context["can_edit_entries"] = is_student(self.request.user) and self.request.user.student == member

        return context


class TimetrackingStatisticsOrgaView(LoginRequiredMixin, TemplateView):
    template_name = "bp/timetracking/statistics_orga.html"
    context_object_name = "statistics_orga"

    def get(self, request, *args, **kwargs):
        if not is_orga(request.user):
            return redirect("bp:index")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = TimeSpentCategory.objects.all()
        charts = [get_hours_per_group()] + [get_hours_per_group(category=c) for c in categories]
        context["hours_per_group_data"] = [
            HoursPerGroupData(cat, chart.get_chart_data(), None, i)
            for cat, chart, i in zip(["Gesamt"] + list(categories.values_list("name", flat=True)),
                                     charts,
                                     range(len(charts)))
        ]
        return context


class TimetrackingStatisticsTLStudentView(LoginRequiredMixin, TemplateView, ProjectByGroupMixin):
    template_name = "bp/timetracking/statistics_tl_student.html"
    context_object_name = "statistics_tl_student"

    def get(self, request, *args, **kwargs):
        if not is_tl_or_student(request.user):
            return redirect("bp:index")
        if is_tl(request.user) and not is_tl_of_group(self.get_object(), request.user):
            messages.add_message(request, messages.WARNING, "Du darfst nur die Zeiten deiner eigenen Gruppe(n) sehen.")
            return redirect("bp:timetracking_tl_start")
        if is_student(request.user) and not is_student_of_group(self.get_object(), request.user):
            messages.add_message(request, messages.WARNING, "Du darfst nur die Zeiten deiner Gruppe sehen.")
            return redirect("bp:index")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        def hours_of_student_in_interval(student, interval):
            hours = \
                interval.timetrackingentry_set.filter(student=student).aggregate(
                    hours=Coalesce(Sum('hours'), Decimal(0)))[
                    'hours']
            return round(hours, 2)

        context = super().get_context_data(**kwargs)
        categories = TimeSpentCategory.objects.all()
        charts = [get_hours_per_group()] + [get_hours_per_group(category=c) for c in categories]
        context["project"] = self.get_object()
        students = context["project"].student_set.all()

        # data for graph 1 (time spent per interval)
        context["hours_per_interval"] = Chart([
            {
                'x': f'{itv.name}',
                'y': f"{sum([hours_of_student_in_interval(s, itv) / len(itv) for s in students])}"
            } for itv in reversed(context["project"].get_past_and_current_intervals)
        ]).get_chart_data()

        # data for remaining graphs (time spent - group comparison: total and for every category)
        if is_tl(self.request.user):
            context["hours_per_group_data"] = [
                HoursPerGroupData(cat, chart.get_chart_data(), chart.single_bar_highlighted(context["project"].nr), i)
                for cat, chart, i in zip(["Gesamt"] + list(categories.values_list("name", flat=True)),
                                         charts,
                                         range(len(charts)))
            ]
        else:
            context["hours_per_group_data"] = None
        return context
