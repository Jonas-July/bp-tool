from bp.templatetags.tags_project_info_misc import ProjectInfoTabTags
from bp.templatetags.tags_project_info_table import ProjectInfoTable

from ...mixins import ProjectGradesMixin

grading_tab = ProjectInfoTabTags(priority=3 * 128)


@grading_tab.register_description('bp/grading/orga/project_info_misc_grading_desc.html')
def grading_description(project):
    tab_context = {'project': project}
    return ProjectGradesMixin.get_grading_context_data(tab_context, project)


@grading_tab.register_content('bp/grading/orga/project_info_misc_grading_content.html')
def grading_content(project):
    tab_context = {'project': project}
    return ProjectGradesMixin.get_grading_context_data(tab_context, project)


@ProjectInfoTable.register('bp/grading/orga/project_info_table_grade_info.html', priority=6 * 128)
def grade_info(project):
    return {
        'project': project,
        'total_points': project.total_points,
        'grade': project.grade,
        'grade_is_close_to_higher_grade': project.grade_close_to_higher_grade,
        'is_complete': project.grade_complete,
        'pitch_points': project.pitch_grade_points,
        'pitch_grade_notes': project.pitch_grade_notes and f"({project.pitch_grade_notes})",
        'ag_points': project.ag_grade_points,
        'docs_points': project.docs_grade_points,
        'docs_grade_notes': project.docs_grade_notes and f"({project.docs_grade_notes})",
    }
