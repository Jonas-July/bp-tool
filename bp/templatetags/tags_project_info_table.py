import heapq

from django import template

from bp.pretix import get_pretix_projectinfo_url

register = template.Library()

class ProjectInfoTable():
    """
            This class collects all info rows for the project info table.
            Each row is defined using a template tag.

            The tags are ordered by priority first and then name.
              Lower value for priority means higher listing
              Equal priority is sorted alphabetically
    """
    registered_rows = []

    @staticmethod
    def get_ordered_infos():
        return map(lambda e: e[1], sorted(ProjectInfoTable.registered_rows))

    @staticmethod
    def register(template_name, *, priority):
        '''
            This decorator registers tags intended for the project info table.
            Tags are registered as inclusion_tags and may take only one required argument
            whose value is the project of interest.

            Example Usage:
            from . import ProjectInfoTable

            @ProjectInfoTable.register('template.html', priority=1)
            def creates_context_based_on_the_project(project):
                return {'project' : project}

            Result:
            Registers a tag that renders template.html with the created context upon calling

            :param template_name: name of the template which will be rendered by the inclusion_tag
            :param priority: priority associated with the tag
            :type priority: int
            :return a decorator to register the tag in this tag set
        '''
        def create_and_register_tag(info_tag):
            tag_name = info_tag.__name__

            @register.inclusion_tag(template_name, takes_context=True, name=tag_name)
            def new_tag(context):
                return info_tag(context['project'])
            heapq.heappush(ProjectInfoTable.registered_rows, (priority, tag_name))
        return create_and_register_tag


@ProjectInfoTable.register('bp/project_info_table_tl_info.html', priority=1)
def tl_info(project):
    return {
        'tl' : project.tl,
    }

@ProjectInfoTable.register('bp/project_info_table_member_info.html', priority=2)
def member_info(project):
    return {
        'student_list'  : project.student_list,
        'student_mails' : project.student_mail,
    }

@ProjectInfoTable.register('bp/project_info_table_ag_info.html', priority=3)
def ag_info(project):
    return {
        'ag'      : project.ag,
        'ag_mail' : project.ag_mail,
    }

@ProjectInfoTable.register('bp/project_info_table_pretix_info.html', priority=4)
def pretix_info(project):
    return {
        'info_url' : get_pretix_projectinfo_url(project),
    }

@ProjectInfoTable.register('bp/project_info_table_grade_info.html', priority=5)
def grade_info(project):
    return {
        'show_aggrade'            : project.ag_points >= 0,
        'ag_points'               : project.ag_points,
        'ag_points_justification' : project.ag_points_justification,
    }

@ProjectInfoTable.register('bp/project_info_table_hours_info.html', priority=6)
def hours_info(project):
    return {
        'project'           : project,
        'total_hours_spent' : project.total_hours,
    }