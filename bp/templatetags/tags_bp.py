from django import template
from django.apps import apps
from django.conf import settings
from django.utils.safestring import mark_safe

from bp.models import TLLog

from .tags_project_info_table import ProjectInfoTable
from .tags_project_info_misc import ProjectInfoTabs

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

@register.tag(name='render')
def render_tag(parser, token):
    """
        Tag for rendering other tags based on their name.
        Since custom tags need to be loaded, their tag set is required.
        Example Usage:
        {% render_tag my_tag my_tag_set %}
        Result is identical to:
        {% load my_tag from my_tag_set %}
        {% my_tag %}
    """
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, tag_to_be_rendered, template_tag_set = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            f"{token.contents.split()[0]} tag requires exactly two arguments"
        )
    return RenderTagNode(tag_to_be_rendered, template_tag_set)

class RenderTagNode(template.Node):
    def __init__(self, tag, template_tag_set):
        self.template_tag_set = template_tag_set
        self.tag = template.Variable(tag)
    def render(self, context):
        tag_name = self.tag.resolve(context)
        template_code = f"{{% load {tag_name} from {self.template_tag_set} %}}{{% {tag_name} %}}"
        return template.Template(template_code).render(context)

@register.inclusion_tag('bp/project_info_table.html', takes_context=True)
def project_info_table(context):
    return {
        'project' : context['project'],
        'infos' : ProjectInfoTable.get_ordered_infos(),
    }

@register.inclusion_tag('bp/project_info_tabs.html', takes_context=True)
def project_info_tabs(context):
    return {
        'project' : context['project'],
        'infos' : ProjectInfoTabs.get_ordered_infos(),
    }
