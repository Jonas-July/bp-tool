from bp.templatetags.tags_project_info_misc import ProjectInfoTabTags

from .view import ProjectGradesMixin

grading_tab = ProjectInfoTabTags(priority=3)

@grading_tab.registerDescription('bp/project_info_misc_grading_desc.html')
def grading_description(project):
    tab_context = {'project' : project}
    return ProjectGradesMixin.get_grading_context_data(tab_context, project)

@grading_tab.registerContent('bp/project_info_misc_grading_content.html')
def grading_content(project):
    tab_context = {'project' : project}
    return ProjectGradesMixin.get_grading_context_data(tab_context, project)
