from enum import Enum

from django import forms

class OrgaGradeCsvImportSpecification(Enum):
    SEPARATOR = ','

    PROJECT = 'nr'
    NOTES = 'notes'
    PITCH_GRADE = 'pitch_grade'
    DOCS_GRADE = 'docs_grade'

class OrgaGradesImportForm(forms.Form):
    Spec = OrgaGradeCsvImportSpecification
    csvfile = forms.FileField(label="Projektliste (CSV)")
