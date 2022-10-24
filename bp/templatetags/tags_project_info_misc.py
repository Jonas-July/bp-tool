from enum import Enum

from django import template

from .registration import generateRegistrationClasses

register = template.Library()


class ProjectInfoTabSpec(Enum):
    """
       Each tab has a description of the tab and
       some tab content based on the project
    """
    DESCRIPTION = ('project',)
    CONTENT = ('project',)

ProjectInfoTabTags, ProjectInfoTabs = generateRegistrationClasses(ProjectInfoTabSpec, register, entities_name="tabs")