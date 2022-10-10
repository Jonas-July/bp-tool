from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic import DetailView

from bp.models import TLLog
from bp.roles import is_orga


class APILogMarkReadView(LoginRequiredMixin, DetailView):
    http_method_names = ['post']
    model = TLLog

    def post(self, request, *args, **kwargs):
        if not is_orga(request.user):
            return HttpResponseForbidden("")
        log = self.get_object()
        log.read = True
        log.save()
        return HttpResponse("")


class APILogMarkHandledView(LoginRequiredMixin, DetailView):
    http_method_names = ['post']
    model = TLLog

    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            log = self.get_object()
            log.handled = True
            log.save()
            return HttpResponse("")
        return HttpResponseForbidden("")


class APILogMarkGoodView(LoginRequiredMixin, DetailView):
    http_method_names = ['post']
    model = TLLog

    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            log = self.get_object()
            log.good_log = True
            log.save()
            return HttpResponse("")
        return HttpResponseForbidden("")


class APILogMarkBadView(LoginRequiredMixin, DetailView):
    http_method_names = ['post']
    model = TLLog

    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            log = self.get_object()
            log.good_log = False
            log.save()
            return HttpResponse("")
        return HttpResponseForbidden("")
