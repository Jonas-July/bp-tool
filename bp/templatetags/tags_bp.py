from django import template
from django.apps import apps
from django.conf import settings
from django.utils.safestring import mark_safe

from bp.models import TLLog

from bp.grading.ag.views import ProjectGradesMixin
from bp.pretix import get_pretix_projectinfo_url

register = template.Library()


# Get Footer Info from settings
@register.simple_tag
def footer_info():
    return settings.FOOTER_INFO


@register.filter
def check_app_installed(name):
    return apps.is_installed(name)


@register.filter
def message_bootstrap_class(tag):
    if tag == "error":
        return "alert-danger"
    elif tag == "success":
        return "alert-success"
    elif tag == "warning":
        return "alert-warning"
    return "alert-info"


@register.filter
def log_status(status):
    if status != "":
        display = TLLog.STATUS_CHOICES[status+2][1]
        color = "#919aa1"
        if status < 0:
            color = "#d9534f"
        elif status > 0:
            color = "#1f9bcf"
        return mark_safe(f'<span style="color:{color}">{display}</span>')
    return ""

@register.inclusion_tag('bp/project_info_table.html', takes_context=True)
def project_info_table(context):
    return {
        'project' : context['project'],
        'info_url' : get_pretix_projectinfo_url(context['project']),
        'total_hours_spent' : context['project'].total_hours,
    }

@register.inclusion_tag('bp/project_info_tabs.html', takes_context=True)
def project_info_tabs(context):
    tab_context = dict()
    tab_context["project"] = context["project"]

    tab_context["logs"] = context["project"].tllog_set.all().prefetch_related("current_problems")
    tab_context["log_count"] = tab_context["logs"].count()

    tab_context["orga_logs"] = context["project"].orgalog_set.all().prefetch_related("current_problems")
    tab_context["orga_log_count"] = tab_context["orga_logs"].count()

    tab_context = ProjectGradesMixin.get_grading_context_data(tab_context, context["project"])

    return tab_context
