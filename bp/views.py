import csv
import io
import datetime
from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.defaults import bad_request, permission_denied, server_error, page_not_found
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, FormView, CreateView, DeleteView

from bp.forms import ProjectImportForm, StudentImportForm, ProjectImportSpecification as ProjectSpec, \
    StudentImportSpecification as StudentSpec
from bp.grading.models import DocsGrade, PitchGrade
from bp.models import BP, Project, Student, TL
from bp.forms import ProjectImportForm as Spec
from bp.roles import is_orga
from bp.timetracking.forms import ProjectPitchPointsUpdateForm, ProjectDocumentationPointsUpdateForm


def error_400(request, exception):
    return bad_request(request, exception, template_name="bp/400.html")


def error_403(request, exception):
    return permission_denied(request, exception, template_name="bp/403.html")


def error_404(request, exception):
    return page_not_found(request, exception, template_name="bp/404.html")


def error_500(request, ):
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
    template_name = "bp/project/project_overview.html"
    context_object_name = "projects"
    permission_required = 'bp.view_project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Projekte"
        return context

    def get_queryset(self):
        return super().get_queryset().select_related('tl').select_related('peer_group').prefetch_related("student_set",
                                                                                                         "tllog_set")


class ProjectUngradedListView(ProjectListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Projekte (Unbewertet)"
        return context

    def get_queryset(self):
        return super().get_queryset().annotate(early_grades=Count('aggradebeforedeadline')).filter(
            Q(early_grades=0) & Q(ag_grade__isnull=True))


class ProjectCloseToHigherGradeListView(ProjectListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Projekte (< 2P. bis zur höheren Note)"
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset_ids = [project.id for project in queryset if project.grade_close_to_higher_grade]
        return queryset.filter(Q(id__in=queryset_ids))


class ProjectView(PermissionRequiredMixin, DetailView):
    model = Project
    template_name = "bp/project/project.html"
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
        context["reminder_count"] = context["tl"].tllogreminder_set.count()
        context["projects"] = context["tl"].project_set.all().prefetch_related("tllog_set",
                                                                               "tllog_set__current_problems")
        return context


class ProjectEditPoints(LoginRequiredMixin, UpdateView):
    template_name = "bp/project/edit_points.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        context["grade_type"] = self.assessment_name
        return context

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, f"{self.assessment_name}-Punkte aktualisiert")
        return reverse_lazy('bp:project_detail', kwargs={'pk': self.object.project.nr})

    def get(self, request, *args, **kwargs):
        if not is_orga(request.user):
            return redirect("bp:index")
        return super().get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return getattr(Project.objects.get(nr=self.kwargs.get("pk")), self.project_field_name)


class ProjectEditPitchPoints(ProjectEditPoints):
    model = PitchGrade
    form_class = ProjectPitchPointsUpdateForm
    context_object_name = "pitch_grade"
    project_field_name = "pitchgrade"
    assessment_name = "Pitch"


class ProjectEditDocumentationPoints(ProjectEditPoints):
    model = DocsGrade
    form_class = ProjectDocumentationPointsUpdateForm
    context_object_name = "documentation_grade"
    project_field_name = "docsgrade"
    assessment_name = "Documentation"


@permission_required("bp.view_student")
def grade_export_view(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Bewertung-AG.csv"'

    writer = csv.writer(response, delimiter=",")
    writer.writerow(['ID', 'Vollständiger Name', 'E-Mail-Adresse', 'Status', 'Gruppe', 'Bewertung', 'Bestwertung',
                     'Bewertung kann geändert werden', 'Zuletzt geändert (Bewertung)', 'Feedback als Kommentar'])

    for student in Student.get_active().filter(project__isnull=False):
        writer.writerow(
            [student.moodle_id, student.name, student.mail, "", student.project.moodle_name, student.project.ag_points,
             100, "Ja", "-", student.project.ag_points_justification])

    return response


class ProjectImportView(PermissionRequiredMixin, FormView):
    template_name = "bp/project/projects_import.html"
    form_class = ProjectImportForm
    success_url = reverse_lazy("bp:project_list")
    permission_required = "bp.add_project"
    extra_context = {'separator': ProjectSpec.SEPARATOR.value,
                     'separator_name': ProjectSpec.SEPARATOR_NAME.value,
                     'project': ProjectSpec.PROJECT.value,
                     'client': ProjectSpec.CLIENT.value,
                     'client_mail': ProjectSpec.CLIENT_MAIL.value,
                     'project_name': ProjectSpec.PROJECT_NAME.value,
                     'short_name': ProjectSpec.PROJECT_SHORT_NAME.value,
                     'pretix_id': ProjectSpec.PRETIX_ID.value
                     }

    def form_valid(self, form):
        import_count = 0
        reader = csv.DictReader(io.TextIOWrapper(form.cleaned_data.get("csvfile").file),
                                delimiter=ProjectSpec.SEPARATOR.value)
        active_bp = BP.get_active()
        lines_ignored = defaultdict(lambda: 0)
        for row in reader:
            '''check if all columns exist'''
            if ProjectSpec.PROJECT.value not in row:
                lines_ignored[f"Spalte '{ProjectSpec.PROJECT.value}' nicht gefunden"] += 1
                continue
            if ProjectSpec.CLIENT.value not in row:
                lines_ignored[f"Spalte '{ProjectSpec.CLIENT.value}' nicht gefunden"] += 1
                continue
            if ProjectSpec.CLIENT_MAIL.value not in row:
                lines_ignored[f"Spalte '{ProjectSpec.CLIENT_MAIL.value}' nicht gefunden"] += 1
                continue
            if ProjectSpec.PROJECT_NAME.value not in row:
                lines_ignored[f"Spalte '{ProjectSpec.PROJECT_NAME.value}' nicht gefunden"] += 1
                continue
            if ProjectSpec.PRETIX_ID.value not in row:
                lines_ignored[f"Spalte '{ProjectSpec.PRETIX_ID.value}' nicht gefunden"] += 1
                continue

            '''try to create object from row'''
            project_nr = row[ProjectSpec.PROJECT.value]
            client = row[ProjectSpec.CLIENT.value]
            client_mail = row[ProjectSpec.CLIENT.value]
            project_name = row[ProjectSpec.PROJECT_NAME.value]
            project_short_name = row[ProjectSpec.PROJECT_SHORT_NAME.value] if not row[ProjectSpec.PROJECT_SHORT_NAME.value] == "" else None
            pretix_id = row[ProjectSpec.PRETIX_ID.value]
            try:
                Project.objects.create(nr=project_nr,
                                       ag=client,
                                       ag_mail=client_mail,
                                       title=project_name,
                                       short_title=project_short_name,
                                       order_id=pretix_id,
                                       bp=active_bp
                                       )
            except IntegrityError:
                print(f"Project mit Nummer '{project_nr}' existiert bereits")
                lines_ignored["Projekt existiert bereits"] += 1
                continue
            except ValueError:
                lines_ignored[f"Ungültiger Wert für '{ProjectSpec.PROJECT.value}' (ValueError)"] += 1
                continue
            else:
                import_count += 1

        '''print success/error messages'''
        messages.add_message(self.request, messages.SUCCESS, f"{import_count} Projekt(e) erfolgreich importiert")
        for error_msg, ignored_lines in lines_ignored.items():
            messages.add_message(self.request, messages.WARNING,
                                 f"{ignored_lines} Zeile(n) ignoriert wegen: {error_msg}")

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
    extra_context = {'separator': StudentSpec.SEPARATOR.value,
                     'separator_name': StudentSpec.SEPARATOR_NAME.value,
                     'id': StudentSpec.ID.value,
                     'name': StudentSpec.NAME.value,
                     'mail': StudentSpec.MAIL.value,
                     'project': StudentSpec.PROJECT.value
                     }

    def form_valid(self, form):
        import_count = 0
        reader = csv.DictReader(io.TextIOWrapper(form.cleaned_data.get("csvfile").file),
                                delimiter=StudentSpec.SEPARATOR.value)
        active_bp = BP.get_active()
        lines_ignored = defaultdict(lambda: 0)
        for row in reader:
            '''check if all columns exist'''
            if StudentSpec.ID.value not in row:
                lines_ignored[f"Spalte '{StudentSpec.ID.value}' nicht gefunden"] += 1
                continue
            if StudentSpec.NAME.value not in row:
                lines_ignored[f"Spalte '{StudentSpec.NAME.value}' nicht gefunden"] += 1
                continue
            if StudentSpec.MAIL.value not in row:
                lines_ignored[f"Spalte '{StudentSpec.MAIL.value}' nicht gefunden"] += 1
                continue
            if StudentSpec.PROJECT.value not in row:
                lines_ignored[f"Spalte '{StudentSpec.PROJECT.value}' nicht gefunden"] += 1
                continue

            '''check if project exists'''
            project_nr = row[StudentSpec.PROJECT.value]
            try:
                project = active_bp.project_set.filter(nr=project_nr).first()
            except ValueError:
                lines_ignored[f"Ungültiger Wert für '{StudentSpec.PROJECT.value}' (ValueError)"] += 1
                continue
            if not project:
                print(f"Project mit Nummer '{project_nr}' existiert nicht")
                lines_ignored["Teilnehmer existiert nicht"] += 1
                continue

            '''try to create object from row'''
            moodle_id = row[StudentSpec.ID.value]
            name = row[StudentSpec.NAME.value]
            mail = row[StudentSpec.MAIL.value]
            try:
                Student.objects.create(moodle_id=moodle_id,
                                       name=name,
                                       mail=mail,
                                       project=project,
                                       bp=active_bp
                                       )
            except IntegrityError:
                print(f"Teilnehmer mit Moodle-ID '{moodle_id}' existiert bereits")
                lines_ignored["Teilnehmer existiert bereits"] += 1
                continue
            else:
                import_count += 1

        '''print success/error messages'''
        messages.add_message(self.request, messages.SUCCESS, f"{import_count} Teilnehmer erfolgreich importiert")
        for error_msg, ignored_lines in lines_ignored.items():
            messages.add_message(self.request, messages.WARNING,
                                 f"{ignored_lines} Zeile(n) ignoriert wegen: {error_msg}")

        return super().form_valid(form)
