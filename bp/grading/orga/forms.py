from datetime import date

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.urls import reverse_lazy

from bp.models import AGGradeBeforeDeadline, AGGradeAfterDeadline
from bp.pretix import get_order_secret


class OrgaGradesImportForm(forms.Form):
    csvfile = forms.FileField(label="Projektliste (CSV)",
                      help_text="CSV-Datei Komma-Separiert. Muss die Spalte 'nr' und 'notes' enthalten, sowie entweder die Spalte 'pitch_grade' oder die Spalte 'docs_grade'")
