from django import forms

from bp.models import TLLog

class TLLogForm(forms.ModelForm):
    class Meta:
        model = TLLog
        fields = ['status', 'current_problems', 'text', 'requires_attention', 'group', 'bp', 'tl']

        widgets = {
            'bp': forms.HiddenInput,
            'tl': forms.HiddenInput,
            'group' : forms.HiddenInput,
            'status': forms.RadioSelect,
            'current_problems': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        """ Grants access to the request object so that only projects of the current user
        are given as options"""

        self.request = kwargs.pop('request')
        super(TLLogForm, self).__init__(*args, **kwargs)
        self.fields['group'].queryset = self.request.user.tl.project_set.all()


class TLLogUpdateForm(forms.ModelForm):
    class Meta:
        model = TLLog
        fields = ['status', 'current_problems', 'text', 'requires_attention']

        widgets = {
            'status': forms.RadioSelect,
            'current_problems': forms.CheckboxSelectMultiple,
        }
