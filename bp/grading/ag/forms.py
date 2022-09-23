from datetime import date

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.urls import reverse_lazy

from bp.models import AGGradeBeforeDeadline, AGGradeAfterDeadline
from bp.pretix import get_order_secret


class AGGradeForm(forms.ModelForm):
    class Meta:
        model = AGGradeBeforeDeadline
        fields = ['ag_points', 'ag_points_justification', 'project']
        widgets = {
            'project'   : forms.HiddenInput(),
            'ag_points' : forms.NumberInput(attrs={'min': 0, 'max': 100, 'step' : 1, 'required': True, 'type': 'number',})
        }

    # Additional fields for information of AG (which project am I currently grading?) and authentication
    project_title = forms.CharField(disabled=True, label="Ihr Project")
    name = forms.CharField(disabled=True, label="Ihr Name")
    secret = forms.CharField(widget=forms.HiddenInput())

    field_order = ['project_title', 'name', 'ag_points', 'ag_points_justification', 'secret', 'project']

    def clean(self):
        cleaned_data = super().clean()

        # Make sure the AG entered a justification and a valid number of points
        # Django already checks if a justification was given and shows error
        # Same with ag_points. If they don't exist here, then Django has detected the issue
        if not (0 <= cleaned_data.get('ag_points', 0) <= 100):
            self.add_error('ag_points', "Die Punktzahl muss zwischen 0 und 100 liegen")

        # Check validity of secret using Pretix
        project = cleaned_data.get('project', None)
        if not project:
            raise ValidationError("Das Projekt ist unbekannt. Ihre Eingabe wurde nicht gespeichert.")
        secret = get_order_secret(project.order_id)
        if not cleaned_data.get('secret', None) or cleaned_data['secret'] != secret:
            raise ValidationError("Authentifizierung fehlgeschlagen. Ihre Eingabe wurde nicht gespeichert.")

        return cleaned_data

    def save(self):
        if date.today() <= self.cleaned_data['project'].bp.ag_grading_end:
            grade = AGGradeBeforeDeadline()
        else:
            grade = AGGradeAfterDeadline()
        grade.project = self.cleaned_data['project']
        grade.ag_points = self.cleaned_data['ag_points']
        grade.ag_points_justification = self.cleaned_data['ag_points_justification']
        grade.save()
        self.instance = grade

    def send_email(self):
        if settings.SEND_MAILS:
            project = self.cleaned_data['project']
            # E-Mail for AGs
            ag_mail = EmailMessage(
                f"[BP-Tool] Neue Bewertung für '{project}' [{self.instance.simple_timestamp}]",
                f"""Es wurde eine neue Bewertung für Ihre Gruppe '{project}' eingetragen. Sie erhalten diese E-Mail, da die Deadline zur Bewertung überschritten wurde.

Die neue Bewertung wurde gespeichert, die Änderungen können aber nur nach entsprechender Absprache mit den Veranstaltern berücksichtigt werden. 
Falls noch nicht geschehen, nehmen Sie daher bitte Kontakt zum BP Orga Team ({settings.SEND_MAILS_TO}) auf.""",
                f"Sent via BP-Tool <{settings.SEND_MAILS_FROM}>",
                [project.ag_mail]
            )
            ag_mail.send(fail_silently=False)

            # E-Mail for Orga team
            url = f"{'https://' + settings.ALLOWED_HOSTS[0] if len(settings.ALLOWED_HOSTS) > 0 else 'http://localhost'}{reverse_lazy('bp:project_detail', kwargs={'pk': project.pk})}"
            orga_mail = EmailMessage(
                f"[BP AG Bewertung] {project} [{self.instance.simple_timestamp}]",
                f"Es wurde eine neue Bewertung für Gruppe {project.nr} ({project}) eingetragen:\n\n {url}",
                f"{self.instance.project.ag} via BP-Tool <{settings.SEND_MAILS_FROM}>",
                [settings.SEND_MAILS_TO],
                reply_to=[project.ag_mail]
            )
            orga_mail.send(fail_silently=False)
