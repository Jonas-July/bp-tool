from django.urls import path

from .views import IndexView, LoginView

index_and_login_patterns = [
    path('', IndexView.as_view(), name="index"),
    path('login/', LoginView.as_view(), name="login"),
]
