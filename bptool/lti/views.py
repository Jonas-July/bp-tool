from django.contrib import messages
from lti_provider.views import LTIRoutingView

from bp.views import BP, TL, Student

class TLRoutingView(LTIRoutingView):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # Login happens in dispatch above
        instance = request.user
        if instance and not TL.objects.filter(user=instance).first():
            TL.objects.create(user=instance, name=f"{instance.first_name} {instance.last_name}", bp=BP.get_active(),
                              confirmed=False)
        return response

class StudentRoutingView(LTIRoutingView):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # Login happens in dispatch above
        instance = request.user
        if instance and instance.email and not Student.objects.filter(user=instance).first():
            associatedStudent = Student.objects.filter(mail=instance.email, bp=BP.get_active()).first()
            if associatedStudent:
                associatedStudent.user = instance
                associatedStudent.save()
            else:
                messages.add_message(self.request, messages.WARNING, "E-Mail-Addresse nicht gefunden. Bitte wende dich an die Veranstalter.")
        return response