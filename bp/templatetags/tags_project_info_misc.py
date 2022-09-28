from django import template

from bp.grading.ag.views import ProjectGradesMixin

register = template.Library()


@register.inclusion_tag('bp/project_info_misc_log_desc.html', takes_context=True)
def log_description(context):
    return {
        'log_count' : context['project'].tllog_set.all().count(),
    }

@register.inclusion_tag('bp/project_info_misc_log_content.html', takes_context=True)
def log_content(context):
    return {
        'status_data' : context['project'].status_json_string,
        'logs'        : context['project'].tllog_set.all(),
        'log_count'   : context['project'].tllog_set.all().count(),
    }

@register.inclusion_tag('bp/project_info_misc_orgalog_desc.html', takes_context=True)
def orgalog_description(context):
    return {
        'orga_log_count' : context['project'].orgalog_set.all().count(),
    }

@register.inclusion_tag('bp/project_info_misc_orgalog_content.html', takes_context=True)
def orgalog_content(context):
    return {
        'orga_logs'        : context['project'].orgalog_set.all(),
        'orga_log_count'   : context['project'].orgalog_set.all().count(),
    }

@register.inclusion_tag('bp/project_info_misc_grading_desc.html', takes_context=True)
def grading_description(context):
    tab_context = {'project' : context['project']}
    return ProjectGradesMixin.get_grading_context_data(tab_context, context['project'])

@register.inclusion_tag('bp/project_info_misc_grading_content.html', takes_context=True)
def grading_content(context):
    tab_context = {'project' : context['project']}
    return ProjectGradesMixin.get_grading_context_data(tab_context, context['project'])
