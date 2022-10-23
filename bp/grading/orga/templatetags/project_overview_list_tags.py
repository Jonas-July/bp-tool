from bp.templatetags.tags_project_overview_list import ProjectOverviewColumnTags

grade_column = ProjectOverviewColumnTags(priority=7*128)

@grade_column.register_description('bp/project/project_overview_list/table_column_grade_desc.html')
def grade_column_description(**kwargs):
    return {}

@grade_column.register_content('bp/project/project_overview_list/table_column_grade_content.html')
def grade_column_content(project, **kwargs):
    return {'pitch'  : project.pitch_grade_points,
            'ag'     : project.ag_grade_points,
            'docs'   : project.docs_grade_points,
           }