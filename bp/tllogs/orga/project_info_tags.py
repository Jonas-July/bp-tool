from bp.templatetags.tags_project_info_misc import ProjectInfoTabTags

tllog_tab = ProjectInfoTabTags(priority=1)

@tllog_tab.register_description('bp/project_info_misc_log_desc.html')
def tllog_description(project):
    return {
        'log_count' : project.tllog_set.all().count(),
    }

@tllog_tab.register_content('bp/project_info_misc_log_content.html')
def tllog_content(project):
    return {
        'status_data' : project.status_json_string,
        'logs'        : project.tllog_set.all(),
        'log_count'   : project.tllog_set.all().count(),
    }
