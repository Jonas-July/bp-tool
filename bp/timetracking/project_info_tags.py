from bp.templatetags.tags_project_info_table import ProjectInfoTable

@ProjectInfoTable.register('bp/timetracking/project_info_table_hours_info.html', priority=6)
def hours_info(project):
    return {
        'project'           : project,
        'total_hours_spent' : project.total_hours,
    }