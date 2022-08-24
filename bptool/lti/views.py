from lti_provider.views import LTIRoutingView

from bp.views import BP, TL

class TLRoutingView(LTIRoutingView):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # Login happens in dispatch above
        instance = request.user
        if instance and not TL.objects.filter(user=instance).first():
            TL.objects.create(user=instance, name=f"{instance.first_name} {instance.last_name}", bp=BP.get_active(),
                              confirmed=False)
        return response