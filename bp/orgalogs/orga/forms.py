from django import forms
from django.core.exceptions import ValidationError

from ..models import OrgaLog

class OrgaLogForm(forms.ModelForm):
    class Meta:
        model = OrgaLog
        fields = ['status', 'current_problems', 'text', 'group', 'bp']

        widgets = {
            'bp': forms.HiddenInput,
            'group' : forms.HiddenInput,
            'status': forms.RadioSelect,
            'current_problems': forms.CheckboxSelectMultiple,
        }
