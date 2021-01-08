from django import forms
from django.core.exceptions import ValidationError

from bp.models import Project
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
