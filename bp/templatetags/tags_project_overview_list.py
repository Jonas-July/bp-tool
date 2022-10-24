from enum import Enum
import heapq

from django import template

from .registration import generateRegistrationClasses

register = template.Library()


class ProjectOverviewColumnSpec(Enum):
    """
       Each column has a description independent of the projects and
       rows of content for each project
    """
    DESCRIPTION = ()
    CONTENT = ('project',)

ProjectOverviewColumnTags, ProjectOverviewList = generateRegistrationClasses(ProjectOverviewColumnSpec, register, entities_name="columns")

def register_pair(*, priority, common_name, description_template, content_template):
    """
    Registers a pair of description and content with default context
    Context is in accordance with the ProjectOverviewColumnSpec
    """
    column = ProjectOverviewColumnTags(priority=priority, common_name=common_name)

    @column.register_description(description_template)
    def column_description(**kwargs):
        return kwargs

    @column.register_content(content_template)
    def column_content(**kwargs):
        return kwargs

register_pair(priority=128, common_name="id_column",
              description_template='bp/project/project_overview_list/table_column_id_desc.html',
              content_template='bp/project/project_overview_list/table_column_id_content.html')

register_pair(priority=2*128, common_name="title_column",
              description_template='bp/project/project_overview_list/table_column_title_desc.html',
              content_template='bp/project/project_overview_list/table_column_title_content.html')

register_pair(priority=4*128, common_name="tl_column",
              description_template='bp/project/project_overview_list/table_column_tl_desc.html',
              content_template='bp/project/project_overview_list/table_column_tl_content.html')

register_pair(priority=5*128, common_name="ag_column",
              description_template='bp/project/project_overview_list/table_column_ag_desc.html',
              content_template='bp/project/project_overview_list/table_column_ag_content.html')

register_pair(priority=6*128, common_name="team_column",
              description_template='bp/project/project_overview_list/table_column_team_desc.html',
              content_template='bp/project/project_overview_list/table_column_team_content.html')
