import json
from datetime import timedelta, date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db import models
from django.db.models import Sum, Max
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.urls import reverse_lazy
from django.utils import timezone, formats

# necessary to register models in database
from bp.grading.models import *
from bp.orgalogs.models import *
from bp.timetracking.models import *
from bp.tllogs.models import *


class BP(models.Model):
    class Meta:
        verbose_name = "BP"
        verbose_name_plural = "BPs"
        ordering = ['-active']

    name = models.CharField(max_length=100, verbose_name="Name", help_text="Titel dieser Iteration")
    moodle_course_id = models.PositiveSmallIntegerField(verbose_name="Moodlekurs-ID",
                                                        help_text="ID des zugehörigen Moodlekurses")
    active = models.BooleanField(verbose_name="Aktiv", help_text="Ist diese Iteration aktuell atkiv?", blank=True)

    pretix_event_ag = models.CharField(max_length=50, verbose_name="Pretix Event Slug (AG)", blank=True)
    pretix_event_tl = models.CharField(max_length=50, verbose_name="Pretix Event Slug (TL)", blank=True)

    ag_grading_start = models.DateField(verbose_name="Beginn der Notenabgabe durch die AGs")
    ag_grading_end = models.DateField(verbose_name="Ende der Notenabgabe durch die AGs")

    @staticmethod
    def get_active():
        return BP.objects.get(active=True)

    def __str__(self):
        if self.active:
            return f"{self.name} (aktiv)"
        return self.name


class Project(models.Model):
    class Meta:
        verbose_name = "Projekt"
        verbose_name_plural = "Projekte"
        ordering = ['bp', 'nr']
        unique_together = [('bp', 'order_id'), ('bp', 'nr')]

    nr = models.PositiveSmallIntegerField(verbose_name="Projekt-/Gruppennummer")
    title = models.CharField(max_length=255, verbose_name="Titel")

    ag = models.CharField(max_length=100, verbose_name="AG")
    ag_mail = models.EmailField(verbose_name="AG E-Mail")
    order_id = models.CharField(max_length=5, verbose_name="Pretix Order ID")

    bp = models.ForeignKey(BP, verbose_name="Zugehöriges BP", on_delete=models.CASCADE)
    tl = models.ForeignKey("TL", verbose_name="Zugehörige TL", on_delete=models.SET_NULL, blank=True, null=True)

    ag_grade = models.ForeignKey("AGGradeAfterDeadline", related_name="valid_grade",
                                 verbose_name="Derzeit gültige Bewertung", on_delete=models.SET_NULL, blank=True,
                                 null=True)

    peer_group = models.ForeignKey("PeerGroup", related_name='projects', verbose_name='Peer Group', blank=True,
                                   on_delete=models.SET_NULL, null=True)

    @staticmethod
    def get_active():
        return Project.objects.filter(bp__active=True)

    @property
    def student_list(self):
        return ", ".join(s.name for s in self.student_set.all())

    @property
    def student_mail(self):
        return ", ".join(s.mail for s in self.student_set.all())

    @property
    def total_hours(self):
        total_hours = sum((s.total_hours for s in self.student_set.all()), Decimal(0))
        return round(total_hours, 2)

    def total_hours_of_category(self, category):
        total_hours = sum((s.total_hours_of_category(category) for s in self.student_set.all()), Decimal(0))
        return round(total_hours, 2)

    @property
    def expected_hours(self):
        expected_hours_per_student = Decimal(270)
        expected_hours = self.student_set.all().count() * expected_hours_per_student
        return round(expected_hours, 2)

    @property
    def get_past_and_current_intervals(self):
        return self.timeinterval_set.order_by("-start").filter(start__lte=date.today()).all()

    @property
    def grade_complete(self):
        return all([self.ag_grade_points, self.pitch_grade_points, self.docs_grade_points])

    @property
    def total_points(self):
        return sum([self.ag_grade_points_value, self.pitch_grade_points_value, self.docs_grade_points_value])

    @property
    def ag_grade_points_value(self):
        return self.ag_points if self.ag_points >= 0 else 0

    @property
    def ag_grade_points(self):
        return formats.localize(self.ag_points, use_l10n=True) if self.ag_points >= 0 else ""

    @property
    def ag_points(self):
        if self.ag_grade:
            return self.ag_grade.ag_points
        recent = self.aggradebeforedeadline_set \
            .order_by('-timestamp').values_list('ag_points', flat=True).first()
        return recent or -1

    @property
    def ag_points_justification(self):
        if self.ag_grade:
            return self.ag_grade.ag_points_justification
        recent = self.aggradebeforedeadline_set \
            .order_by('-timestamp').values_list('ag_points_justification', flat=True).first()
        return recent or ""

    @property
    def most_recent_ag_points(self):
        after_deadline = self.aggradeafterdeadline_set \
            .order_by('-timestamp').values_list('ag_points', flat=True).first()

        before_deadline = self.aggradebeforedeadline_set \
            .order_by('-timestamp').values_list('ag_points', flat=True).first()

        return after_deadline or before_deadline or -1

    @property
    def most_recent_ag_points_justification(self):
        after_deadline = self.aggradeafterdeadline_set \
            .order_by('-timestamp').values_list('ag_points_justification', flat=True).first()

        before_deadline = self.aggradebeforedeadline_set \
            .order_by('-timestamp').values_list('ag_points_justification', flat=True).first()

        return after_deadline or before_deadline or ""

    @property
    def pitch_grade_points_value(self):
        pitch_grade = hasattr(self, 'pitchgrade') and self.pitchgrade
        return pitch_grade and round(pitch_grade.grade_points, 2) or 0

    @property
    def pitch_grade_points(self):
        pitch_grade = hasattr(self, 'pitchgrade') and self.pitchgrade
        return pitch_grade and formats.localize(round(pitch_grade.grade_points, 2), use_l10n=True) or ""

    @property
    def pitch_grade_notes(self):
        pitch_grade = hasattr(self, 'pitchgrade') and self.pitchgrade
        return pitch_grade and str(pitch_grade.grade_notes) or ""

    @property
    def docs_grade_points_value(self):
        docs_grade = hasattr(self, 'docsgrade') and self.docsgrade
        return docs_grade and round(docs_grade.grade_points, 2) or 0

    @property
    def docs_grade_points(self):
        docs_grade = hasattr(self, 'docsgrade') and self.docsgrade
        return docs_grade and formats.localize(round(docs_grade.grade_points, 2), use_l10n=True) or ""

    @property
    def docs_grade_notes(self):
        docs_grade = hasattr(self, 'docsgrade') and self.docsgrade
        return docs_grade and str(docs_grade.grade_notes) or ""

    @property
    def status_json_string(self):
        return json.dumps(
            [{'x': log.simple_timestamp, 'y': log.status} for log in self.tllog_set.all().order_by('timestamp')])

    @staticmethod
    def without_recent_logs(projects=None):
        if not projects:
            projects = Project.get_active()
        remind_after_days = timedelta(days=settings.LOG_REMIND_PERIOD_DAYS) + timedelta(days=1)
        latest_day_to_remind = timezone.now() - remind_after_days
        projects_not_covered = projects.annotate(last_log_date=Coalesce(Max('tllog__timestamp'), latest_day_to_remind)) \
            .filter(last_log_date__lte=latest_day_to_remind).all()
        return projects_not_covered

    def __str__(self):
        return f"{self.nr}: {self.title}"

    @property
    def moodle_name(self):
        return f"{self.nr:02d}_{self.title}"


class PeerGroup(models.Model):
    class Meta:
        verbose_name = "Peergruppe"
        verbose_name_plural = "Peergruppen"
        ordering = ['bp', 'nr']
        unique_together = [('bp', 'nr')]

    nr = models.PositiveSmallIntegerField(verbose_name="Nummer")

    bp = models.ForeignKey(BP, verbose_name="Zugehöriges BP", on_delete=models.CASCADE)

    def __str__(self):
        return f"Peergroup {self.nr:02}"

    @property
    def member_groups(self):
        return "\n".join(str(p) for p in self.projects.all())


class TL(models.Model):
    class Meta:
        verbose_name = "Teamleitung"
        verbose_name_plural = "Teamleitungen"
        ordering = ['bp', 'name']

    name = models.CharField(verbose_name="Name", max_length=100)
    bp = models.ForeignKey(BP, verbose_name="Zugehöriges BP", on_delete=models.CASCADE)
    user = models.OneToOneField(verbose_name="Account", to=User, on_delete=models.DO_NOTHING, blank=True, null=True)
    confirmed = models.BooleanField(verbose_name="Bestätigt", default=False, blank=True)

    @staticmethod
    def get_active():
        return TL.objects.filter(bp__active=True, confirmed=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    class Meta:
        verbose_name = "Teilnehmende*r"
        verbose_name_plural = "Teilnehmende"
        ordering = ['bp', 'name']
        unique_together = ['moodle_id']

    name = models.CharField(verbose_name="Name", max_length=100)
    moodle_id = models.CharField(verbose_name="Moodle ID", max_length=50, blank=True)
    mail = models.EmailField(verbose_name="E-Mail", blank=True)
    user = models.OneToOneField(verbose_name="Account", to=User, on_delete=models.DO_NOTHING, blank=True, null=True)
    bp = models.ForeignKey(BP, verbose_name="Zugehöriges BP", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Projekt")

    @staticmethod
    def get_active():
        return Student.objects.filter(bp__active=True)

    @property
    def total_hours(self):
        total_hours = self.timetrackingentry_set.filter(interval__group=self.project).aggregate(
            total_hours=Coalesce(Sum('hours'), Decimal(0)))['total_hours']
        return round(total_hours, 2)

    def total_hours_of_category(self, category):
        total_hours = self.timetrackingentry_set.filter(interval__group=self.project, category=category).aggregate(
            total_hours=Coalesce(Sum('hours'), Decimal(0)))['total_hours']
        return round(total_hours, 2)

    def __str__(self):
        return self.name
