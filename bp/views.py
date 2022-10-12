import csv
import io
import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.mail import EmailMessage
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.defaults import bad_request, permission_denied, server_error, page_not_found
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, FormView, CreateView, DeleteView

from bp.grading.ag.views import ProjectGradesMixin

from bp.forms import ProjectImportForm, StudentImportForm
from bp.models import BP, Project, Student, TL, TLLog, OrgaLog


def error_400(request, exception):
    return bad_request(request, exception, template_name="bp/400.html")

def error_403(request, exception):
    return permission_denied(request, exception, template_name="bp/403.html")

def error_404(request, exception):
    return page_not_found(request, exception, template_name="bp/404.html")

def error_500(request,):
    return server_error(request, template_name="bp/500.html")


class FilterByActiveBPMixin:
    def __init__(self) -> None:
        self.active_bp = BP.get_active()
        super().__init__()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bp'] = self.active_bp
        return context

    def get_queryset(self):
        return super().get_queryset().filter(bp=self.active_bp)


class ProjectListView(PermissionRequiredMixin, FilterByActiveBPMixin, ListView):
    model = Project
    template_name = "bp/project_overview.html"
    context_object_name = "projects"
    permission_required = 'bp.view_project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Projekte"
        return context

    def get_queryset(self):
        return super().get_queryset().select_related('tl').prefetch_related("student_set", "tllog_set")

class ProjectUngradedListView(ProjectListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Projekte (Unbewertet)"
        return context

    def get_queryset(self):
        return super().get_queryset().annotate(early_grades=Count('aggradebeforedeadline')).filter(Q(early_grades=0) & Q(ag_grade__isnull=True))


class ProjectView(PermissionRequiredMixin, ProjectGradesMixin, DetailView):
    model = Project
    template_name = "bp/project.html"
    context_object_name = "project"
    permission_required = 'bp.view_project'


class TLListView(PermissionRequiredMixin, FilterByActiveBPMixin, ListView):
    model = TL
    template_name = "bp/tl_overview.html"
    context_object_name = "tls"
    permission_required = 'bp.view_tl'

    def get_queryset(self):
        return super().get_queryset().filter(confirmed=True).prefetch_related("project_set", "tllog_set")


class TLView(PermissionRequiredMixin, DetailView):
    model = TL
    template_name = "bp/tl.html"
    context_object_name = "tl"
    permission_required = 'bp.view_tl'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["logs"] = context["tl"].tllog_set.all()
        context["logs_count"] = context["logs"].count()
        context["logs_count_good"] = context["tl"].tllog_set.filter(good_log=True).count()
        context["logs_count_bad"] = context["tl"].tllog_set.filter(good_log=False).count()
        context["reminder_count"] = context["tl"].tllogreminder_set.count()
        context["projects"] = context["tl"].project_set.all().prefetch_related("tllog_set", "tllog_set__current_problems")
        return context


class OrgaLogView(PermissionRequiredMixin, DetailView):
    model = OrgaLog
    template_name = "bp/orgalog.html"
    context_object_name = "log"
    permission_required = "bp.view_orgalog"


@permission_required("bp.view_student")
def grade_export_view(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Bewertung-AG.csv"'

    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Vollständiger Name', 'E-Mail-Adresse', 'Status', 'Gruppe', 'Bewertung', 'Bestwertung', 'Bewertung kann geändert werden', 'Zuletzt geändert (Bewertung)', 'Feedback als Kommentar'])

    for student in Student.get_active().filter(project__isnull=False):
        writer.writerow([student.moodle_id, student.name, student.mail, "", student.project.moodle_name, student.project.ag_points, 100, "Ja", "-", student.project.ag_points_justification])

    return response


class ProjectImportView(PermissionRequiredMixin, FormView):
    template_name = "bp/projects_import.html"
    form_class = ProjectImportForm
    success_url = reverse_lazy("bp:project_list")
    permission_required = "bp.add_project"

    def form_valid(self, form):
        import_count = 0
        reader = csv.DictReader(io.TextIOWrapper(form.cleaned_data.get("csvfile").file), delimiter=";")
        active_bp = BP.get_active()
        for row in reader:
            try:
                Project.objects.create(**{
                    "nr": row["nr"],
                    "ag": row["ag"],
                    "ag_mail": row["ag_mail"],
                    "title": row["title"],
                    "order_id": row["order_id"],
                    "bp": active_bp,
                })
                print(f"Projekt {row['title']} importiert")
                import_count += 1
            except IntegrityError:
                print(f"Projekt {row['title']} existiert bereits")
        messages.add_message(self.request, messages.SUCCESS, f"{import_count} Projekt(e) erfolgreich importiert")
        return super().form_valid(form)


class StudentListView(PermissionRequiredMixin, FilterByActiveBPMixin, ListView):
    model = Student
    template_name = "bp/student_overview.html"
    context_object_name = "students"
    permission_required = 'bp.view_student'

    def get_queryset(self):
        return super().get_queryset().select_related('project')


class StudentImportView(PermissionRequiredMixin, FormView):
    template_name = "bp/students_import.html"
    form_class = StudentImportForm
    success_url = reverse_lazy("bp:student_list")
    permission_required = "bp.add_student"

    def form_valid(self, form):
        import_count = 0
        reader = csv.DictReader(io.TextIOWrapper(form.cleaned_data.get("csvfile").file), delimiter=",")
        active_bp = BP.get_active()
        for row in reader:
            try:
                if not row["Gruppe"].startswith("Nicht Mitglied einer Gruppe"):
                    project = Project.objects.get(nr=row["Gruppe"].split("_")[0])
                    Student.objects.create(**{
                        "name": row["Vollständiger Name"],
                        "moodle_id": row["ID"],
                        "mail": row["E-Mail-Adresse"],
                        "project": project,
                        "bp": active_bp,
                    })
                    print(f"Teilnehmer*in {row['Vollständiger Name']} importiert")
                    import_count += 1
            except IntegrityError:
                print(f"Teilnehmer*in {row['Vollständiger Name']} existiert bereits")
        messages.add_message(self.request, messages.SUCCESS, f"{import_count} Teilnehmende erfolgreich importiert")
        return super().form_valid(form)


class APILogMarkReadView(LoginRequiredMixin, DetailView):
    http_method_names = ['post']
    model = TLLog

    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            log = self.get_object()
            log.read = True
            log.save()
            return HttpResponse("")
        return HttpResponseForbidden("")


class APILogMarkHandledView(LoginRequiredMixin, DetailView):
    http_method_names = ['post']
    model = TLLog

    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            log = self.get_object()
            log.handled = True
            log.save()
            return HttpResponse("")
        return HttpResponseForbidden("")


class APILogMarkGoodView(LoginRequiredMixin, DetailView):
    http_method_names = ['post']
    model = TLLog

    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            log = self.get_object()
            log.good_log = True
            log.save()
            return HttpResponse("")
        return HttpResponseForbidden("")


class APILogMarkBadView(LoginRequiredMixin, DetailView):
    http_method_names = ['post']
    model = TLLog

    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            log = self.get_object()
            log.good_log = False
            log.save()
            return HttpResponse("")
        return HttpResponseForbidden("")
