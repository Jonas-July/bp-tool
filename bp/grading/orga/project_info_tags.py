from bp.templatetags.tags_project_info_misc import ProjectInfoTabTags
from bp.templatetags.tags_project_info_table import ProjectInfoTable

from ..mixins import ProjectGradesMixin

grading_tab = ProjectInfoTabTags(priority=3*128)

@grading_tab.register_description('bp/grading/orga/project_info_misc_grading_desc.html')
def grading_description(project):
    tab_context = {'project' : project}
    return ProjectGradesMixin.get_grading_context_data(tab_context, project)

@grading_tab.register_content('bp/grading/orga/project_info_misc_grading_content.html')
def grading_content(project):
    tab_context = {'project' : project}
    return ProjectGradesMixin.get_grading_context_data(tab_context, project)


@ProjectInfoTable.register('bp/grading/orga/project_info_table_grade_info.html', priority=6*128)
def grade_info(project):
    return {
        'show_aggrade'            : project.ag_points >= 0,
        'ag_points'               : project.ag_points,
        'ag_points_justification' : project.ag_points_justification,
    }
