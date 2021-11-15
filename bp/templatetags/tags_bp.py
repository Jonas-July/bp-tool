from django import template
from django.apps import apps
from django.conf import settings
from django.utils.safestring import mark_safe

from bp.models import TLLog

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
        print(display)
        color = "#919aa1"
        if status < 0:
            color = "#d9534f"
        elif status > 0:
            color = "#1f9bcf"
        return mark_safe(f'<span style="color:{color}">{display}</span>')
    return ""
