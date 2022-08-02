from datetime import timedelta

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import TimeInterval, TimeTrackingEntry


class TimeIntervalForm(forms.ModelForm):
    class Meta:
        model = TimeInterval
        fields = ['group', 'name', 'start', 'end']

        widgets = {
            'group': forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        """ Grants access to the request object so that only projects of the current user
        are given as options"""

        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        self.fields['group'].queryset = self.request.user.tl.project_set.all()

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data['end'] < cleaned_data['start']:
            return self.add_error('end', "Ende muss später als Beginn sein")

        return cleaned_data

class TimeIntervalEntryForm(forms.ModelForm):
    class Meta:
        model = TimeTrackingEntry
        fields = ['category', 'hours', 'interval']

        widgets = {
            'interval': forms.HiddenInput,
            'hours'   : forms.NumberInput(attrs={'min': 0, 'max': 999, 'step' : 0.25, 'required': True, 'type': 'number',})
        }

    def __init__(self, *args, **kwargs):
        """ Grants access to the request object so that only projects of the current user
        are given as options"""

        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        self.fields['interval'].queryset = self.request.user.student.project.timeinterval_set.order_by('-start')

    def clean(self):
        cleaned_data = super().clean()

        cleaned_data['student'] = self.request.user.student
        try:
            if cleaned_data['student'] not in cleaned_data['interval'].group.student_set.all():
                raise ValidationError("Ungültiges Intervall angegeben")
        except KeyError:
            raise ValidationError("Ungültiges Intervall angegeben")

        if cleaned_data.get('hours', 0) < 0:
            self.add_error('hours', "Stundenzahl muss nicht-negativ sein")

        if not cleaned_data.get('category', None):
            self.add_error('category', "Bitte gib eine Kategorie an")

        return cleaned_data

    def save(self):
        obj, created = TimeTrackingEntry.objects.update_or_create(student =self.cleaned_data['student'],
                                                                  interval=self.cleaned_data['interval'],
                                                                  category=self.cleaned_data['category'],
                                                                  defaults={'hours' : self.cleaned_data['hours']})

        self.instance = obj
