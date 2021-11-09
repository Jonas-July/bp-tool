from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.urls import reverse_lazy


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

    ag_points = models.SmallIntegerField(verbose_name="Punkte für den Implementierungsteil", help_text="0-100",
                                         default=-1)
    ag_points_justification = models.TextField(verbose_name="Begründung", blank=True)

    @staticmethod
    def get_active():
        return Project.objects.filter(bp=BP.get_active())

    @property
    def student_list(self):
        return ", ".join(s.name for s in self.student_set.all())

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
        return TL.objects.filter(bp=BP.get_active(), confirmed=True)

    def __str__(self):
        return self.name


@receiver(post_save, sender=User)
def update_profile_signal(sender, instance: User, created, **kwargs):
    if created:
        TL.objects.create(user=instance, name=f"{instance.first_name} {instance.last_name}", bp=BP.get_active(),
                          confirmed=False)


class Student(models.Model):
    class Meta:
        verbose_name = "Teilnehmende*r"
        verbose_name_plural = "Teilnehmende"
        ordering = ['bp', 'name']

    name = models.CharField(verbose_name="Name", max_length=100)
    moodle_id = models.CharField(verbose_name="Moodle ID", max_length=50, blank=True)
    mail = models.EmailField(verbose_name="E-Mail", blank=True)
    bp = models.ForeignKey(BP, verbose_name="Zugehöriges BP", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Projekt")

    @staticmethod
    def get_active():
        return Student.objects.filter(bp=BP.get_active())

    def __str__(self):
        return self.name


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
    handled = models.BooleanField(blank=True, default=False, verbose_name="Erledigt", help_text="Das Log forderte eine Reaktion des Orga-Teams, die bereits durchgeführt wurde.")

    @property
    def simple_timestamp(self):
        return self.timestamp.strftime('%d.%m.%y %H:%M')

    @property
    def problems(self):
        problems_string = ", ".join(str(p) for p in self.current_problems.all())
        return problems_string if problems_string != "" else "-"

    def __str__(self):
        return f"{self.tl} für Gruppe {self.group.nr} am {self.simple_timestamp}"


@receiver(post_save, sender=TLLog)
def update_tllog_receiver(sender, instance: TLLog, created, **kwargs):
    if created and settings.SEND_MAILS and instance.requires_attention:
        # Send an email for new important logs
        url = f"{settings.ALLOWED_HOSTS[0] if len(settings.ALLOWED_HOSTS) > 0 else 'http://localhost'}{reverse_lazy('bp:log_detail', kwargs={'pk': instance.pk})}"
        send_mail(
            f"[BP TL Logs] {instance.group} ({instance.simple_timestamp})",
            f"Achtung, folgendes Log erfordert besondere Aufmerksamkeit\n\n{url}\n\nProbleme:{instance.problems}\n\n{instance.text}",
            settings.SEND_MAILS_FROM,
            [settings.SEND_MAILS_TO],
            fail_silently=True
        )


class TLLogProblem(models.Model):
    class Meta:
        verbose_name = "TL-Log-Problem"
        verbose_name_plural = "TL-Log-Probleme"

    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name
