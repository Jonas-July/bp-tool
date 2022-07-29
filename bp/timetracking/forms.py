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
