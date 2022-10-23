from bp.templatetags.tags_project_overview_list import ProjectOverviewColumnTags

status_column = ProjectOverviewColumnTags(priority=3*128)

@status_column.register_description('bp/project/project_overview_list/table_column_status_desc.html')
def status_column_description(**kwargs):
    return {}

@status_column.register_content('bp/project/project_overview_list/table_column_status_content.html')
def status_column_content(project, **kwargs):
    most_recent_tllog = project.tllog_set.order_by('-timestamp').first()
    status = most_recent_tllog.status if most_recent_tllog else ""
    return {'status' : status}
