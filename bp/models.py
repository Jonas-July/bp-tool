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
from django.utils.datetime_safe import datetime

from bp.timetracking.models import *

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

    ag_grade = models.ForeignKey("AGGradeAfterDeadline", related_name="valid_grade", verbose_name="Derzeit gültige Bewertung", on_delete=models.SET_NULL, blank=True, null=True)

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

    @property
    def get_past_and_current_intervals(self):
        return self.timeinterval_set.order_by("-start").filter(start__lte=date.today()).all()

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
    def status_json_string(self):
        return json.dumps([{'x': log.simple_timestamp, 'y': log.status} for log in self.tllog_set.all().order_by('timestamp')])

    @staticmethod
    def without_recent_logs(projects=None):
        if not projects:
            projects = Project.get_active()
        remind_after_days = timedelta(days=settings.LOG_REMIND_PERIOD_DAYS) + timedelta(days=1)
        latest_day_to_remind = datetime.now() - remind_after_days
        projects_not_covered = projects.annotate(last_log_date=Coalesce(Max('tllog__timestamp'), latest_day_to_remind))\
                                       .filter(last_log_date__lte=latest_day_to_remind).all()
        return projects_not_covered

    def __str__(self):
        return f"{self.nr}: {self.title}"

    @property
    def moodle_name(self):
        return f"{self.nr:02d}_{self.title}"


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


class AGGrade(models.Model):
    class Meta:
        abstract = True
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    ag_points = models.SmallIntegerField(verbose_name="Punkte für den Implementierungsteil", help_text="0-100")
    ag_points_justification = models.TextField(verbose_name="Begründung")
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)

    @property
    def simple_timestamp(self):
        return self.timestamp.strftime('%d.%m.%y %H:%M')

    @staticmethod
    def get_active():
        return TLLog.objects.filter(bp__active=True)

class AGGradeBeforeDeadline(AGGrade):
    class Meta:
        verbose_name = "Bewertung"
        verbose_name_plural = "Bewertungen"
        ordering = ['project', 'timestamp']

    def __str__(self):
        return f"Bewertung für Projekt {self.project.nr} am {self.simple_timestamp}"

class AGGradeAfterDeadline(AGGrade):
    class Meta:
        verbose_name = "Bewertung (verspätet)"
        verbose_name_plural = "Bewertungen (verspätet)"
        ordering = ['project', 'timestamp']

    def __str__(self):
        return f"Verspätete Bewertung für Projekt {self.project.nr} am {self.simple_timestamp}"


class Student(models.Model):
    class Meta:
        verbose_name = "Teilnehmende*r"
        verbose_name_plural = "Teilnehmende"
        ordering = ['bp', 'name']

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
        total_hours = self.timetrackingentry_set.aggregate(total_hours=Coalesce(Sum('hours'), Decimal(0)))['total_hours']
        return round(total_hours, 2)

    def __str__(self):
        return self.name

class OrgaLog(models.Model):
    class Meta:
        verbose_name = "Orga-Log"
        verbose_name_plural = "Orga-Logs"
        ordering = ['-timestamp']

    STATUS_CHOICES = [
        (-2, 'Schlecht'),
        (-1, 'Eher schlecht'),
        (0, 'Neutral'),
        (1, 'Eher gut'),
        (2, 'Gut'),
    ]

    bp = models.ForeignKey(BP, on_delete=models.CASCADE)
    group = models.ForeignKey(Project, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)
    status = models.SmallIntegerField(
        choices=STATUS_CHOICES,
        default=0,
        help_text="Wie läuft es bei der Gruppe insgesamt aktuell?"
    )
    current_problems = models.ManyToManyField(verbose_name="Aktuelle Probleme", to="TLLogProblem", blank=True, help_text="Trifft davon etwas bei der Gruppe zu?")
    text = models.TextField(
        help_text="Notizen zur Gruppe"
    )

    @property
    def tl(self):
        return self.group.tl

    @property
    def simple_timestamp(self):
        return self.timestamp.strftime('%d.%m.%y %H:%M')

    @property
    def problems(self):
        problems_string = ", ".join(str(p) for p in self.current_problems.all())
        return problems_string if problems_string != "" else "-"

    @staticmethod
    def get_active():
        return TLLog.objects.filter(bp__active=True)

    def __str__(self):
        return f"Notiz der Orga für Gruppe {self.group.nr} am {self.simple_timestamp}"


class TLLog(models.Model):
    class Meta:
        verbose_name = "TL-Log"
        verbose_name_plural = "TL-Logs"
        ordering = ['-timestamp']

    STATUS_CHOICES = [
        (-2, 'Schlecht'),
        (-1, 'Eher schlecht'),
        (0, 'Neutral'),
        (1, 'Eher gut'),
        (2, 'Gut'),
    ]

    bp = models.ForeignKey(BP, on_delete=models.CASCADE)
    group = models.ForeignKey(Project, on_delete=models.CASCADE)
    tl = models.ForeignKey(TL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)
    status = models.SmallIntegerField(
        choices=STATUS_CHOICES,
        default=0,
        help_text="Wie läuft es bei der Gruppe insgesamt aktuell?"
    )
    current_problems = models.ManyToManyField(verbose_name="Aktuelle Probleme", to="TLLogProblem", blank=True, help_text="Trifft davon etwas bei der Gruppe zu?")
    text = models.TextField(
        help_text="Berichte kurz: Was war die Aktivität vergangene Woche? Hast du dich mit der Gruppe getroffen? Hattet ihr anderweitig Kontakt? Gab es ein AG Treffen? Gibt es Probleme?"
    )
    requires_attention = models.BooleanField(verbose_name="Besondere Aufmerksamkeit", blank=True, default=False, help_text="Benötigt diese Gruppe aktuell besondere Aufmerksamkeit durch das Organisationsteam/sollten wir das Log besonders dringend lesen?")
    comment = models.TextField(blank=True, verbose_name="Kommentar", help_text="Interner Kommentar des Orga-Teams zu diesem Eintrag")
    read = models.BooleanField(blank=True, default=False, verbose_name="Gelesen")
    handled = models.BooleanField(blank=True, default=False, verbose_name="Erledigt", help_text="Das Log forderte eine Reaktion des Orga-Teams, die bereits durchgeführt wurde.")
    good_log = models.NullBooleanField(blank=True, default=None, verbose_name="Gutes Log?")

    @property
    def simple_timestamp(self):
        return self.timestamp.strftime('%d.%m.%y %H:%M')

    @property
    def problems(self):
        problems_string = ", ".join(str(p) for p in self.current_problems.all())
        return problems_string if problems_string != "" else "-"

    @staticmethod
    def get_active():
        return TLLog.objects.filter(bp__active=True)

    def __str__(self):
        return f"{self.tl} für Gruppe {self.group.nr} am {self.simple_timestamp}"


@receiver(post_save, sender=TLLog)
def update_tllog_receiver(sender, instance: TLLog, created, **kwargs):
    if created and settings.SEND_MAILS and instance.requires_attention:
        # Send an email for new important logs
        url = f"{'https://' + settings.ALLOWED_HOSTS[0] if len(settings.ALLOWED_HOSTS) > 0 else 'http://localhost'}{reverse_lazy('bp:log_detail', kwargs={'pk': instance.pk})}"
        mail = EmailMessage(
            f"[BP TL Logs] {instance.group} ({instance.simple_timestamp})",
            f"Achtung, folgendes Log von {instance.tl} erfordert besondere Aufmerksamkeit:\n\n{url}\n\n{instance.text}",
            f"{instance.tl} via BP-Tool <{settings.SEND_MAILS_FROM}>",
            [settings.SEND_MAILS_TO],
            reply_to=[instance.tl.user.email]
        )
        mail.send(fail_silently=True)


class TLLogProblem(models.Model):
    class Meta:
        verbose_name = "TL-Log-Problem"
        verbose_name_plural = "TL-Log-Probleme"

    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class TLLogReminder(models.Model):
    class Meta:
        verbose_name = "TL-Log-Erinnerung"
        verbose_name_plural = "TL-Log-Erinnerungen"

    bp = models.ForeignKey(BP, on_delete=models.CASCADE)
    group = models.ForeignKey(Project, on_delete=models.CASCADE)
    tl = models.ForeignKey(TL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)

    @property
    def simple_timestamp(self):
        return self.timestamp.strftime('%d.%m.%y %H:%M')

    def __str__(self):
        return f"{self.simple_timestamp}: {self.group.nr} - {self.tl}"
