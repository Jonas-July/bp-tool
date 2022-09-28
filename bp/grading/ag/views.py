import datetime

from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, CreateView

from .forms import AGGradeForm
from bp.models import Project
from bp.pretix import get_order_secret

class ProjectByOrderIDMixin:
    def get_object(self, queryset=None):
        return Project.objects.get(order_id=self.kwargs["order_id"])

class ProjectGradesMixin:
    @staticmethod
    def get_grading_context_data(context, project):
        beforedeadline = project.aggradebeforedeadline_set.all().order_by("-timestamp")
        afterdeadline = project.aggradeafterdeadline_set.all().order_by("-timestamp")
        context["gradings_before"] = beforedeadline
        context["gradings_after"] = afterdeadline
        context["gradings_before_count"] = context["gradings_before"].count()
        context["gradings_after_count"] = context["gradings_after"].count()
        context["gradings_count"] = context["gradings_before_count"] + context["gradings_after_count"]
        context["valid_grade_after"] = (project.ag_grade and project.ag_grade.pk) or None
        context["valid_grade_before"] = None if (context["valid_grade_after"] or not beforedeadline.first()) \
                                        else beforedeadline.first().pk
        return context

class AGGradeView(ProjectByOrderIDMixin, ProjectGradesMixin, CreateView):
    model = Project
    form_class = AGGradeForm
    template_name = "bp/project_grade.html"
    context_object_name = "project"

    def deadline_passed(self):
        return self.get_object().bp.ag_grading_end < datetime.date.today()

    def form_valid(self, form):
        redirect = super().form_valid(form)
        if self.deadline_passed():
            form.send_email()
        return redirect

    def get_success_url(self):
        return reverse("bp:ag_grade_success", kwargs={"order_id": self.get_object().order_id})

    def _get_secret_from_url(self):
        return self.kwargs.get("secret", "")

    def get(self, request, *args, **kwargs):
        # Redirect if secret is invalid
        object = self.get_object()
        if self._get_secret_from_url() != get_order_secret(object.order_id):
            return redirect("bp:ag_grade_invalid")

        if datetime.date.today() < object.bp.ag_grading_start:
            return redirect("bp:ag_grade_too_early", order_id=object.order_id)

        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initials = super().get_initial()
        object = self.get_object()

        # Populate with previous grading
        # Show empty field instead of default value of -1 as this might confuse the AGs
        initials["ag_points"] = object.most_recent_ag_points if object.ag_points > -1 else ""
        initials["ag_points_justification"] = object.most_recent_ag_points_justification

        # Populate information fields for AG (will not be used for updating)
        initials["project_title"] = object.title
        initials["name"] = object.ag

        # Populate hidden secret field
        initials["secret"] = self._get_secret_from_url()
        initials["project"] = object
        return initials

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context = self.get_grading_context_data(context, self.get_object())
        return context

class AGGradeSuccessView(ProjectByOrderIDMixin, ProjectGradesMixin, DetailView):
    model = Project
    context_object_name = "project"
    template_name = "bp/project_grade_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        deadline = self.get_object().bp.ag_grading_end
        context["after_deadline"] = deadline < datetime.date.today()
        context["deadline"] = deadline

        context = self.get_grading_context_data(context, self.get_object())
        return context


class AGGradeEarlyView(ProjectByOrderIDMixin, DetailView):
    model = Project
    context_object_name = "project"
    template_name = "bp/project_grade_early.html"
