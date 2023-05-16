from django import forms


class ProjectImportForm(forms.Form):
    csvfile = forms.FileField(label="Projektliste (CSV)")


class StudentImportForm(forms.Form):
    csvfile = forms.FileField(label="Teilnehmendenliste (CSV)")