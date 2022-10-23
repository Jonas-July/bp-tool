from enum import Enum
import heapq

from django import template

register = template.Library()


class ProjectOverviewColumnSpec(Enum):
    """
       Each column has a description independent of the projects and
       rows of content for each project
    """
    DESCRIPTION = ()
    CONTENT = ('project',)


class ProjectOverviewColumnTags():
    """
        This class registers tags intended for the project overview list.
        Tags are registered as inclusion_tags and may take only the arguments as
        specified by the ProjectOverviewColumnSpec.
        Each column has a description tag and a content tag who must both exist before
        the tags are finally registered

        Example Usage:

        from . import ProjectOverviewColumnTags
        overview_column = ProjectOverviewColumnTags(priority=1)

        @overview_column.register_description('template_desc.html')
        def creates_description_context(**kwargs):
            return {}

        @overview_column.register_content('template_content.html')
        def creates_content_context_based_on_the_project(project, **kwargs):
            return {'project' : project}

        Result:
        Registers two tags that render their templates with the created context upon calling
        Tags can be retrieved via ProjectOverviewList.get_ordered_columns()
    """
    def __init__(self, *, priority, common_name=None):
        self.priority = priority
        self.common_name = common_name
        self.tags = {type : None for type in ProjectOverviewColumnSpec}

    def register_if_available(self):
        if all([val != None for val in self.tags.values()]):
            ProjectOverviewList.create_and_register_tags(*self.tags.values(), priority=self.priority)

    def create_and_register_tag(self, tag_type, template_name):
        def decorator(tag):
            tag_name = f"{self.common_name}_{tag_type.name.lower()}" if self.common_name else tag.__name__
            self.tags[tag_type] = (tag, tag_name, tag_type, template_name)
            self.register_if_available()
            return tag
        return decorator

    def register_description(self, template_name):
        tag_type = ProjectOverviewColumnSpec.DESCRIPTION
        return self.create_and_register_tag(tag_type, template_name)

    def register_content(self, template_name):
        tag_type = ProjectOverviewColumnSpec.CONTENT
        return self.create_and_register_tag(tag_type, template_name)


class ProjectOverviewList():
    """
        This class collects the columns for the project overview list.

        The columns are ordered by priority first and then name.
          Lower value for priority means earlier listing in get_ordered_columns
          Equal priority is sorted alphabetically
    """
    registered_columns = []

    @staticmethod
    def get_ordered_columns():
        return list(map(lambda e: e[1], sorted(ProjectOverviewList.registered_columns)))

    @staticmethod
    def create_and_register_tags(*tags, priority):
        """
            Registers a set of tags who are used simultaneously.
            Each argument must be of the form
            (tag, tag_name, tag_type, template_name) where tag_type is an enum member
                whose value is a list of parameters the tag must expect

            :param tags: tags to be registered
            :type tags: list of (tag, tag_name, tag_type, template_name)
            :param priority: priority associated with the tags
            :type priority: real numeric
            :return None
        """
        def register_tag(tag, params, template_name, tag_name):
            @register.inclusion_tag(template_name, takes_context=True, name=tag_name)
            def new_tag(context):
                return tag(**{param : context[param] for param in params})

        tag_names = list(map(lambda tag_tuple : tag_tuple[1], tags))
        for (tag, tag_name, tag_type, template_name) in tags:
            register_tag(tag, tag_type.value, template_name, tag_name)
        heapq.heappush(ProjectOverviewList.registered_columns, (priority, tag_names))

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
