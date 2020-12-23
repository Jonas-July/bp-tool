from django.urls import path
from django.views.generic import TemplateView

app_name = "bp"

urlpatterns = [
    path('', TemplateView.as_view(template_name="bp/base.html"), name="index"),
]
