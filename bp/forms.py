from django import forms
from django.core.exceptions import ValidationError

from bp.models import Project, TLLog, BP, TL
from bp.pretix import get_order_secret


class AGGradeForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['ag_points', 'ag_points_justification']

    # Additional fields for information of AG (which project am I currently grading?) and authentication
    project = forms.CharField(disabled=True, label="Ihr Project")
    name = forms.CharField(disabled=True, label="Ihr Name")
    secret = forms.CharField(widget=forms.HiddenInput())

    field_order = ['project', 'name', 'ag_points', 'ag_points_justification', 'secret']

    def clean(self):
        cleaned_data = super().clean()

        # Make sure the AG entered a justification and a valid number of points
        if cleaned_data['ag_points_justification'] == "":
            self.add_error('ag_points_justification', "Bitte geben Sie eine Begründung ein")
        if not (0 <= cleaned_data['ag_points'] <= 100):
            self.add_error('ag_points', "Die Punktzahl muss zwischen 0 und 100 liegen")

        # Check validity of secret using Pretix
        secret = get_order_secret(self.instance.order_id)
        if cleaned_data['secret'] != secret:
            raise ValidationError("Authentifizierung fehlgeschlagen. Ihre Eingabe wurde nicht gespeichert.")

        return cleaned_data


class ProjectImportForm(forms.Form):
    csvfile = forms.FileField(label="Projektliste (CSV)",
                      help_text="CSV-Datei Semikolon-Separiert. Muss die Spalten nr, ag, ag_mail, title, order_id enthalten")


class StudentImportForm(forms.Form):
    csvfile = forms.FileField(label="Teilnehmendenliste (CSV)",
                      help_text="CSV-Datei Komma-Separiert. Muss die Spalten ID, Vollständiger Name, E-Mail-Adresse, Gruppe enthalten")


class TLLogForm(forms.ModelForm):
    class Meta:
        model = TLLog
        fields = ['status', 'current_problems', 'text', 'requires_attention', 'group', 'bp', 'tl']

        widgets = {
            'bp': forms.HiddenInput,
            'tl': forms.HiddenInput,
            'status': forms.RadioSelect,
            'current_problems': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        """ Grants access to the request object so that only projects of the current user
        are given as options"""

        self.request = kwargs.pop('request')
        super(TLLogForm, self).__init__(*args, **kwargs)
        self.fields['group'].queryset = Project.objects.filter(
            tl=self.request.user.tl)
        self.fields['bp'].queryset = BP.objects.filter(active=True)
        self.fields['tl'].queryset = TL.objects.filter(pk=self.request.user.tl.pk)


class TLLogUpdateForm(forms.ModelForm):
    class Meta:
        model = TLLog
        fields = ['status', 'current_problems', 'text', 'requires_attention']

        widgets = {
            'status': forms.RadioSelect,
            'current_problems': forms.CheckboxSelectMultiple,
        }
