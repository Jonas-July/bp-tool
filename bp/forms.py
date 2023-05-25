from enum import Enum

from django import forms


class ProjectImportSpecification(Enum):
    SEPARATOR = ';'
    SEPARATOR_NAME = 'Semikolon'

    PROJECT = 'nr'
    CLIENT = 'ag'
    CLIENT_MAIL = 'ag_mail'
    PROJECT_NAME = 'titel'
    PRETIX_ID = 'order_id'


class ProjectImportForm(forms.Form):
    Spec = ProjectImportSpecification
    csvfile = forms.FileField(label="Projektliste (CSV)")


class StudentImportSpecification(Enum):
    SEPARATOR = ';'
    SEPARATOR_NAME = 'Semikolon'

    ID = 'ID'
    NAME = 'Name'
    MAIL = 'E-Mail-Adresse'
    PROJECT = 'Gruppe'


class StudentImportForm(forms.Form):
    Spec = StudentImportSpecification
    csvfile = forms.FileField(label="Teilnehmendenliste (CSV)")
