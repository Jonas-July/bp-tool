from datetime import date

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.forms.utils import ErrorList

from bp.models import Project, TLLog, BP, TL, TLLogReminder


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


class LogReminderForm(forms.Form):
    projects = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)

    def send_reminders(self):
        mail_counter = 0
        for project_key in self.cleaned_data["projects"]:
            project = Project.objects.get(pk=project_key)
            if project is not None and project.tl is not None and project.tl.user is not None and project.tl.user.email:
                mail = EmailMessage(
                    f"[BP TL Logs] Erinnerung: Bitte ein Log für {project} schreiben",
                    f"Hallo {project.tl},\n\nfür deine Gruppe '{project.title}' ({project.nr}) wurde seit mindestens {settings.LOG_REMIND_PERIOD_DAYS} Tagen kein Log mehr geschrieben. Bitte trage zeitnah den aktuellen Stand im System ein.",
                    settings.SEND_MAILS_FROM,
                    [project.tl.user.email],
                    reply_to=[settings.SEND_MAILS_TO]
                )
                mail.send(fail_silently=False)
                TLLogReminder.objects.create(
                    bp=project.bp,
                    group=project,
                    tl=project.tl
                )
                mail_counter += 1
        return f"{str(mail_counter)} Erinnerungsmails verschickt"

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList, label_suffix=None, empty_permitted=False, field_order=None, use_required_attribute=None, renderer=None):
        super().__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, field_order, use_required_attribute, renderer)
        self.fields["projects"].choices = self.initial["project_choices"]
        self.fields["projects"].initial = [k for k, _ in self.initial["project_choices"]]
