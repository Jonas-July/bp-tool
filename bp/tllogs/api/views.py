from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic import DetailView

from bp.models import TLLog
from bp.roles import is_orga
from bp.tllogs.models import TLLogEvaluation


class APILogMark(LoginRequiredMixin, DetailView):
    http_method_names = ['post']
    model = TLLog

    def mark(self):
        return None

    def post(self, request, *args, **kwargs):
        if not is_orga(request.user):
            return HttpResponseForbidden("")
        log = self.get_object()
        self.mark(log)
        log.save()
        return HttpResponse("")


class APILogMarkReadView(APILogMark):
    def mark(self, log):
        log.read = True


class APILogMarkHandledView(APILogMark):
    def mark(self, log):
        log.handled = True


class APILogRate(LoginRequiredMixin, DetailView):
    http_method_names = ['post']
    model = TLLog

    def post(self, request, *args, **kwargs):
        if not is_orga(request.user):
            return HttpResponseForbidden("")

        log = self.get_object()
        evaluation = TLLogEvaluation.get_rating_of(log, request.user)

        if evaluation:
            evaluation.rating = request.POST['rating']
            evaluation.save()
        else:
            TLLogEvaluation.objects.create(bp=log.bp,
                                           log=log,
                                           rater=request.user,
                                           rating=request.POST['rating']
                                           )

        return HttpResponse(TLLogEvaluation.average_rating_of(log))
