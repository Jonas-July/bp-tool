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

from .forms import OrgaGradesImportForm, OrgaGradeCsvImportSpecification as Spec
from ..models import PitchGrade, DocsGrade

# necessary to load the custom tags
from .templatetags import project_info_tags, project_overview_list_tags


class OrgaGradesImportView(LoginRequiredMixin, FormView):
    template_name = "bp/grading/orga/grades_import.html"
    form_class = OrgaGradesImportForm
    success_url = reverse_lazy("bp:project_list")
    extra_context = {'separator': Spec.SEPARATOR.value,
                     'separator_name': Spec.SEPARATOR_NAME.value,
                     'project': Spec.PROJECT.value,
                     'pitch_notes': Spec.PITCH_NOTES.value,
                     'docs_notes': Spec.DOCS_NOTES.value,
                     'pitch_grade': Spec.PITCH_GRADE.value,
                     'docs_grade': Spec.DOCS_GRADE.value
                     }

    def form_valid(self, form):
        """
        For a version using the match statement, see below
        """
        pitch_import_count = 0
        docs_import_count = 0
        reader = csv.DictReader(io.TextIOWrapper(form.cleaned_data.get("csvfile").file), delimiter=Spec.SEPARATOR.value)
        active_bp = BP.get_active()
        lines_ignored = defaultdict(lambda: 0)
        grading_ignored = defaultdict(lambda: 0)

        '''return if neither pitch nor docs grade columns exist'''
        has_pitch_col = Spec.PITCH_GRADE.value in reader.fieldnames
        has_docs_col = Spec.DOCS_GRADE.value in reader.fieldnames
        if not (has_pitch_col or has_docs_col):
            messages.add_message(self.request, messages.WARNING,
                                 f"Alle Zeile(n) ignoriert wegen: Spalten '{Spec.PITCH_GRADE.value}' oder '{Spec.DOCS_GRADE.value}' nicht gefunden")
            return super().form_valid(form)

        for row in reader:
            '''check if all columns exist'''
            if Spec.PROJECT.value not in row:
                lines_ignored[f"Spalte '{Spec.PROJECT.value}' nicht gefunden"] += 1
                continue
            if has_pitch_col and Spec.PITCH_NOTES.value not in row:
                lines_ignored[f"Spalte '{Spec.PITCH_NOTES.value}' nicht gefunden"] += 1
                continue
            if has_docs_col and Spec.DOCS_NOTES.value not in row:
                lines_ignored[f"Spalte '{Spec.DOCS_NOTES.value}' nicht gefunden"] += 1
                continue
            if has_pitch_col and Spec.PITCH_GRADE.value not in row:
                lines_ignored[f"Spalte '{Spec.PITCH_GRADE.value}' nicht gefunden"] += 1
                continue
            if has_docs_col and Spec.DOCS_GRADE.value not in row:
                lines_ignored[f"Spalte '{Spec.DOCS_GRADE.value}' nicht gefunden"] += 1
                continue

            '''check if project exists'''
            nr = row[Spec.PROJECT.value]
            try:
                project = active_bp.project_set.filter(nr=nr).first()
            except ValueError:
                lines_ignored[f"Ungültiger Wert für '{Spec.PROJECT.value}' (ValueError)"] += 1
                continue
            if not project:
                print(f"Project mit Nummer '{nr}' existiert nicht")
                lines_ignored["Projekt existiert nicht"] += 1
                continue

            '''try to create object(s) from row'''
            if has_pitch_col:
                if not 0 <= float(row[Spec.PITCH_GRADE.value]) <= 20:
                    grading_ignored[f"Ungültiger Wert für '{Spec.PITCH_GRADE.value}' (Der Wert muss eine Zahl zwischen 0 und 20 sein.)"] += 1
                else:
                    try:
                        PitchGrade.objects.create(project=project,
                                                  grade_points=row[Spec.PITCH_GRADE.value],
                                                  grade_notes=row[Spec.PITCH_NOTES.value])
                    except IntegrityError:
                        grading_ignored[f"Bewertung aus Spalte '{Spec.PITCH_GRADE.value}' existiert bereits"] += 1
                    except ValidationError:
                        grading_ignored[f"Ungültiger Wert für '{Spec.PITCH_GRADE.value}' (Der Wert muss eine Zahl zwischen 0 und 20 sein.)"] += 1
                    else:
                        pitch_import_count += 1
            if has_docs_col:
                if not 0 <= float(row[Spec.DOCS_GRADE.value]) <= 80:
                    grading_ignored[f"Ungültiger Wert für '{Spec.DOCS_GRADE.value}' (Der Wert muss eine Zahl zwischen 0 und 80 sein.)"] += 1
                else:
                    try:
                        DocsGrade.objects.create(project=project,
                                                 grade_points=row[Spec.DOCS_GRADE.value],
                                                 grade_notes=row[Spec.DOCS_GRADE.value])
                    except IntegrityError:
                        grading_ignored[f"Bewertung aus Spalte '{Spec.DOCS_GRADE.value}' existiert bereits"] += 1
                    except ValidationError:
                        grading_ignored[f"Ungültiger Wert für '{Spec.DOCS_GRADE.value}' (Der Wert muss eine Zahl zwischen 0 und 80 sein.)"] += 1
                    else:
                        docs_import_count += 1

        '''print success/error messages'''
        messages.add_message(self.request, messages.SUCCESS,
                             f"{pitch_import_count} Pitch-Bewertung(en) und {docs_import_count} Dokumentations-Bewertung(en) erfolgreich importiert")
        for error_msg, ignored_lines in lines_ignored.items():
            messages.add_message(self.request, messages.WARNING,
                                 f"{ignored_lines} Zeile(n) ignoriert wegen: {error_msg}")
        for error_msg, ignored_lines in grading_ignored.items():
            messages.add_message(self.request, messages.WARNING,
                                 f"{ignored_lines} Bewertung(en) ignoriert wegen: {error_msg}")

        return super().form_valid(form)

    '''
    def form_valid_py3p10(self, form):
        """
        This version isn't supported in the current dashboard. It would need some changes to be used.
        
        This version of form_valid uses the match statement
        which is only available in 3.10+
        """
        import_count = 0
        reader = csv.DictReader(io.TextIOWrapper(form.cleaned_data.get("csvfile").file), delimiter=Spec.SEPARATOR.value)
        active_bp = BP.get_active()
        lines_ignored = defaultdict(lambda:0)
        for row in reader:
            match row:
                case {Spec.PROJECT.value : nr, Spec.NOTES.value : notes}:
                    project = active_bp.project_set.filter(nr=nr).first()
                    if not project:
                        print(f"Project mit Nummer '{nr}' existiert nicht")
                        lines_ignored["Projekt existiert nicht"] += 1
                        continue
                    match row:
                        case {Spec.PITCH_GRADE.value : grade_points} | {Spec.DOCS_GRADE.value : grade_points}:
                            match row:
                                case {Spec.PITCH_GRADE.value : _}:
                                    grade_type = PitchGrade
                                case {Spec.DOCS_GRADE.value : _}:
                                    grade_type = DocsGrade

                            try:
                                grade_type.objects.create(project=project,
                                                      grade_points=grade_points,
                                                      grade_notes=notes)
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
                            lines_ignored[f"Spalten '{Spec.PITCH_GRADE.value}' und '{Spec.DOCS_GRADE.value}' nicht gefunden"] += 1
                            continue
                case {}:
                    lines_ignored[f"Spalten '{Spec.PROJECT.value}' und/oder '{Spec.NOTES.value}' nicht gefunden"] += 1
                    continue
        messages.add_message(self.request, messages.SUCCESS, f"{import_count} Projekt(e) erfolgreich importiert")
        for error_msg, ignored_lines in lines_ignored.items():
            messages.add_message(self.request, messages.WARNING, f"{ignored_lines} Zeile(n) ignoriert wegen: {error_msg}")
        return super().form_valid(form)
    '''
