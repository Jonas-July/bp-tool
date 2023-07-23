from enum import Enum

from django import forms


class OrgaGradeCsvImportSpecification(Enum):
    SEPARATOR = ';'
    SEPARATOR_NAME = 'Semikolon'

    PROJECT = 'nr'
    PITCH_NOTES = 'pitch_notizen'
    DOCS_NOTES = 'documentation_notizen'
    PITCH_GRADE = 'pitch_punkte'
    DOCS_GRADE = 'documentation_punkte'


class OrgaGradesImportForm(forms.Form):
    Spec = OrgaGradeCsvImportSpecification
    csvfile = forms.FileField(label="Projektliste (CSV)")
