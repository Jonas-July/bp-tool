from bp.templatetags.tags_project_info_misc import ProjectInfoTabTags

orgalog_tab = ProjectInfoTabTags(priority=2)

@orgalog_tab.register_description('bp/orgalogs/orga/project_info_misc_orgalog_desc.html')
def orgalog_description(project):
    return {
        'orga_log_count' : project.orgalog_set.all().count(),
    }

@orgalog_tab.register_content('bp/orgalogs/orga/project_info_misc_orgalog_content.html')
def orgalog_content(project):
    return {
        'orga_logs'      : project.orgalog_set.all(),
        'orga_log_count' : project.orgalog_set.all().count(),
        'group'          : project,
    }
