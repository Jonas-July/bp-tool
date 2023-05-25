from enum import Enum

from django import forms


class OrgaGradeCsvImportSpecification(Enum):
    SEPARATOR = ';'
    SEPARATOR_NAME = 'Semikolon'

    PROJECT = 'nr'
    NOTES = 'notizen'
    PITCH_GRADE = 'pitch_grade'
    DOCS_GRADE = 'documentation_grade'


class OrgaGradesImportForm(forms.Form):
    Spec = OrgaGradeCsvImportSpecification
    csvfile = forms.FileField(label="Projektliste (CSV)")
