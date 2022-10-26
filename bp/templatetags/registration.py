from collections import namedtuple

TagType = namedtuple("Tag", ('name', 'parameters'))

def generateRegistrationClasses(enum_specification, register, entities_name="entities"):
    """
        Generates classes for registration

        Example Usage based on the project info tabs:
        # template tag registration

        from enum import Enum
        from django import template
        from .registration import generateRegistrationClasses

        register = template.Library()

        class ProjectInfoTabSpec(Enum):
            DESCRIPTION = ('project',)
            CONTENT = ('project',)

        ProjectInfoTabTags, ProjectInfoTabs = generateRegistrationClasses(ProjectInfoTabSpec, register, entities_name="infos")

        ##################################################################
        # Now, each subsystem can declare its own tab based on above spec:

        from . import ProjectInfoTabTags

        tllog_tab = ProjectInfoTabTags(priority=1)

        @tllog_tab.register_description('bp/tllogs/orga/project_info_misc_log_desc.html')
        def tllog_description(project):
            return {
                'log_count' : project.tllog_set.all().count(),
            }

        @tllog_tab.register_content('bp/tllogs/orga/project_info_misc_log_content.html')
        def tllog_content(project):
            return {
                'status_data' : project.status_json_string,
                'logs'        : project.tllog_set.all(),
                'log_count'   : project.tllog_set.all().count(),
            }

        ####################################################################
        # And finally, the tab template tag can request all registered tabs:

        from . import ProjectInfoTabs

        register = template.Library()

        @register.inclusion_tag('bp/project/project_info/tabs.html', takes_context=True)
        def project_info_tabs(context):
            return {
                'project' : context['project'],
                'infos' : ProjectInfoTabs.get_ordered_infos(),
            }

    """
    specification = list(TagType(name, enum.value) for name, enum in enum_specification.__members__.items())
    class DynamicStructureEntityTagsRegistration():
        """
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
            self.tags = {type : None for type in specification}

        def register_if_available(self):
            if all([val != None for val in self.tags.values()]):
                DynamicStructure.create_and_register_tags(*self.tags.values(), priority=self.priority)

        def create_and_register_tag(self, tag_type, template_name):
            def inner(tag):
                tag_name = f"{self.common_name}_{tag_type.name.lower()}" if self.common_name else tag.__name__
                self.tags[tag_type] = (tag, tag_name, tag_type.parameters, template_name)
                self.register_if_available()
                return tag
            return inner

        def __getattr__(self, name):
            prefix = 'register_'
            if not name.startswith(prefix):
                raise AttributeError(name)
            requested_type = name[len(prefix):]
            for type in specification:
                if requested_type == type.name.lower():
                    tag_type = type
                    return lambda template_name: self.create_and_register_tag(tag_type, template_name)
            raise AttributeError(f"'{requested_type}' is not specified by '{specification.__name__}'")

    class NamedOrderedEntities(type):
        def __getattr__(cls, name):
            prefix = 'get_ordered_'
            if not name.startswith(prefix):
                raise AttributeError(name)
            requested_entity_name = name[len(prefix):]
            if requested_entity_name == entities_name:
                return cls.get_ordered_entities
            raise AttributeError(requested_entity_name)

    class DynamicStructure(metaclass=NamedOrderedEntities):
        """
            This class collects the entities for the dynamic structure.

            The entities are ordered by priority first and then name.
              Lower value for priority means earlier listing in get_ordered_entities
              Equal priority is sorted alphabetically
        """
        registered_entities = []
        changed = True

        @staticmethod
        def get_ordered_entities():
            if DynamicStructure.changed:
                DynamicStructure.registered_entities = sorted(DynamicStructure.registered_entities)
                DynamicStructure.changed = False
            return list(map(lambda e: e[1], DynamicStructure.registered_entities))

        @staticmethod
        def create_and_register_tags(*tags, priority):
            """
                Registers a set of tags who are used simultaneously.
                Each argument must be of the form
                (tag, tag_name, parameters, template_name) where parameters is a tuple
                    of parameters the tag must expect

                :param tags: tags to be registered
                :type tags: list of (tag, tag_name, parameters, template_name)
                :param priority: priority associated with the tags
                :type priority: real numeric
                :return None
            """
            def register_tag(tag, params, template_name, tag_name):
                @register.inclusion_tag(template_name, takes_context=True, name=tag_name)
                def new_tag(context):
                    return tag(**{param : context[param] for param in params})

            tag_names = list(map(lambda tag_tuple : tag_tuple[1], tags))
            for (tag, tag_name, parameters, template_name) in tags:
                register_tag(tag, parameters, template_name, tag_name)
            DynamicStructure.registered_entities.append((priority, tag_names))
            DynamicStructure.changed = True

    return DynamicStructureEntityTagsRegistration, DynamicStructure
