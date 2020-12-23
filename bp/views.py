from django.views.generic import TemplateView, ListView, DetailView

from bp.models import BP, Project, Student, TL


class ActiveBPMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bp'] = BP.get_active()
        return context


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


class IndexView(ActiveBPMixin, TemplateView):
    template_name = "bp/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = Project.get_active()
        context['tls'] = TL.get_active()
        context['students'] = Student.get_active()
        context['students_without_project'] = Student.get_active().filter(project=None)
        return context


class ProjectListView(FilterByActiveBPMixin, ListView):
    model = Project
    template_name = "bp/project_overview.html"
    context_object_name = "projects"


class ProjectView(DetailView):
    model = Project
    template_name = "bp/project.html"
    context_object_name = "project"


class TLListView(FilterByActiveBPMixin, ListView):
    model = TL
    template_name = "bp/tl_overview.html"
    context_object_name = "tls"


class TLView(DetailView):
    model = TL
    template_name = "bp/tl.html"
    context_object_name = "tl"
