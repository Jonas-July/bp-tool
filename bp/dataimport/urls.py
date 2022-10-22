from django.urls import path

from .views import DataImportView

import_patterns = [
    path('', DataImportView.as_view(), name="import_overview"),
]
