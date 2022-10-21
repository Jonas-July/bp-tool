from collections import defaultdict
import csv
import io

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse_lazy
from django.views.generic import FormView

from bp.models import BP

from .forms import OrgaGradesImportForm
from ..models import PitchGrade, DocsGrade

# necessary to load the project info tags
from . import project_info_tags

class OrgaGradesImportView(LoginRequiredMixin, FormView):
    template_name = "bp/grading/orga/grades_import.html"
    form_class = OrgaGradesImportForm
    success_url = reverse_lazy("bp:project_list")

    def form_valid(self, form):
        import_count = 0
        separator = ','
        reader = csv.DictReader(io.TextIOWrapper(form.cleaned_data.get("csvfile").file), delimiter=separator)
        active_bp = BP.get_active()
        lines_ignored = defaultdict(lambda:0)
        for row in reader:
            match row:
                case {'nr' : nr, 'justification' : justification}:
                    project = active_bp.project_set.filter(nr=nr).first()
                    if not project:
                        print(f"Project mit Nummer '{nr}' existiert nicht")
                        lines_ignored["Projekt existiert nicht"] += 1
                        continue
                    match row:
                        case {'pitch_grade' : grade_points} | {'docs_grade' : grade_points}:
                            match row:
                                case {'pitch_grade' : _}:
                                    grade_type = PitchGrade
                                case {'docs_grade' : _}:
                                    grade_type = DocsGrade

                            try:
                                grade_type.objects.create(project=project,
                                                      grade_points=grade_points,
                                                      grade_justification=justification)
                            except IntegrityError:
                                print(f"Bewertung des Typs {grade_type} für Projekt {project} existiert bereits")
                                lines_ignored["Bewertung existiert bereits"] += 1
                                continue
                            except ValidationError:
                                lines_ignored[f"Ungültiger Wert für die Bewertung (ValidationError)"] += 1
                                continue
                            else:
                                import_count += 1
                        case {}:
                            lines_ignored["Spalten 'pitch_grade' und 'docs_grade' nicht gefunden"] += 1
                            continue
                case {}:
                    lines_ignored["Spalten 'nr' und/oder 'justification' nicht gefunden"] += 1
                    continue
        messages.add_message(self.request, messages.SUCCESS, f"{import_count} Projekt(e) erfolgreich importiert")
        for error_msg, ignored_lines in lines_ignored.items():
            messages.add_message(self.request, messages.WARNING, f"{ignored_lines} Zeile(n) ignoriert wegen: {error_msg}")
        return super().form_valid(form)
