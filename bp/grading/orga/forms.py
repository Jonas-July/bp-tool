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
    csvfile = forms.FileField(label="Projektliste (CSV)",
                      help_text=f"""CSV-Datei Komma-Separiert. \
Muss die Spalten '{Spec.PROJECT.value}' und '{Spec.NOTES.value}' enthalten, \
sowie entweder die Spalte '{Spec.PITCH_GRADE.value}' oder die Spalte '{Spec.DOCS_GRADE.value}'""")
