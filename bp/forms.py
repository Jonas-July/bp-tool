from django import forms


class ProjectImportForm(forms.Form):
    csvfile = forms.FileField(label="Projektliste (CSV)",
                      help_text="CSV-Datei Semikolon-Separiert. Muss die Spalten nr, ag, ag_mail, title, order_id enthalten")


class StudentImportForm(forms.Form):
    csvfile = forms.FileField(label="Teilnehmendenliste (CSV)",
                      help_text="CSV-Datei Komma-Separiert. Muss die Spalten ID, Vollständiger Name, E-Mail-Adresse, Gruppe enthalten")