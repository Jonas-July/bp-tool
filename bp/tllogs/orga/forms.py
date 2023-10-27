import datetime
import json

from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.forms.utils import ErrorList

from bp.models import Project, TL


class LogReminderForm(forms.Form):
    tls = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)

    def send_reminders(self):
        for tl_key in self.cleaned_data["tls"]:
            tl_key = json.loads(tl_key)
            tl = TL.objects.get(pk=tl_key[0])
            if tl.user is not None and tl.user.email:
                mail = EmailMessage(
                    f"[BP TL Logs] Erinnerung: Bitte Log(s) für Projekt(e) schreiben",
                    f"Hallo {tl},\n\nfür deine Gruppe(n) {', '.join([Project.objects.get(pk=p_id).short_title_else_title for p_id in tl_key[1]])} wurde(n) seit mindestens {tl_key[2]} Tagen kein Log mehr geschrieben. Bitte trage zeitnah den aktuellen Stand im System ein.",
                    settings.SEND_MAILS_FROM,
                    [tl.user.email],
                    reply_to=[settings.SEND_MAILS_TO]
                )
                mail.send(fail_silently=False)

                for p_id in tl_key[1]:
                    project = Project.objects.get(pk=p_id)
                    project.last_reminded = datetime.datetime.now()
                    project.save()

                tl.log_reminder += 1
                tl.save()

        return f"{len(self.cleaned_data['tls'])} Erinnerungsmail(s) verschickt"

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList, label_suffix=None, empty_permitted=False, field_order=None, use_required_attribute=None, renderer=None):
        super().__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, field_order, use_required_attribute, renderer)
        self.fields["tls"].choices = self.initial["tl_choices"]
        self.fields["tls"].initial = [k for k, _ in self.initial["tl_choices"]]
