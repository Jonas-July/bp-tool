import heapq

from django import template

register = template.Library()


class ProjectInfoTabTags():
    """
        This class registers tags intended for the project info tabs.
        Tags are registered as inclusion_tags and may take only one required argument
        whose value is the project of interest.
        Each tab has a description tag and a content tab who must both exist before
        the tags are registered

        Example Usage:

        from . import ProjectInfoTabTags
        info_tab = ProjectInfoTabTags(priority=1)

        @info_tab.register_description('template_desc.html')
        def creates_description_context_based_on_the_project(project):
            return {'project' : project}

        @info_tab.register_content('template_content.html')
        def creates_content_context_based_on_the_project(project):
            return {'project' : project}

        Result:
        Registers two tags that render their templates with the created context upon calling
        Tags can be retrieved via ProjectInfoTabs.get_ordered_infos()
    """
    def __init__(self, *, priority):
        self.priority = priority
        self.description = None
        self.content = None

    def register_if_available(self):
        if self.description and self.content:
            ProjectInfoTabs.create_and_register_tags(self.description, self.content, priority=self.priority)

    def register_description(self, template_name):
        def create_and_register_tag(info_tag):
            self.description = (info_tag, template_name)
            self.register_if_available()
            return info_tag
        return create_and_register_tag

    def register_content(self, template_name):
        def create_and_register_tag(info_tag):
            self.content = (info_tag, template_name)
            self.register_if_available()
            return info_tag
        return create_and_register_tag


class ProjectInfoTabs():
    """
        This class collects the descriptions and the content for the project info tabs.
        Each tab is defined using two template tags, one for the description and one for the content.
        The tags are ordered by priority first and then name.
          Lower value for priority means higher listing (further to the left)
          Equal priority is sorted alphabetically
    """
    registered_tabs = []

    @staticmethod
    def get_ordered_infos():
        return list(map(lambda e: e[1], sorted(ProjectInfoTabs.registered_tabs)))

    @staticmethod
    def create_and_register_tags(*info_tags, priority):
        """
            Registers a set of tags who are used simultaneously.
            Each argument must be of the form
            (info_tag, template_name)

            :param info_tags: tags to be registered
            :type info_tags: list of (info_tag, template_name)
            :param priority: priority associated with the tags
            :type priority: int
            :return None
        """
        tag_names = list(map(lambda tag: tag[0].__name__, info_tags))
        for (info_tag, template_name), tag_name in zip(info_tags, tag_names):

            @register.inclusion_tag(template_name, takes_context=True, name=tag_name)
            def new_tag(context):
                return info_tag(context['project'])
        heapq.heappush(ProjectInfoTabs.registered_tabs, (priority, tag_names))
