from django.db import models


class BP(models.Model):
    class Meta:
        verbose_name = "BP"
        verbose_name_plural = "BPs"
        ordering = ['-active']

    name = models.CharField(max_length=100, verbose_name="Name", help_text="Titel dieser Iteration")
    moodle_course_id = models.PositiveSmallIntegerField(verbose_name="Moodlekurs-ID", help_text="ID des zugehörigen Moodlekurses")
    active = models.BooleanField(verbose_name="Aktiv", help_text="Ist diese Iteration aktuell atkiv?", blank=True)

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

    nr = models.PositiveSmallIntegerField(verbose_name="Projekt-/Gruppennummer")
    title = models.CharField(max_length=255, verbose_name="Titel")

    ag = models.CharField(max_length=100, verbose_name="AG")
    ag_mail = models.EmailField(verbose_name="AG E-Mail")
    order_id = models.CharField(max_length=5, verbose_name="Pretix Order ID")

    bp = models.ForeignKey(BP, verbose_name="Zugehöriges BP", on_delete=models.CASCADE)
    tl = models.ForeignKey("TL", verbose_name="Zugehörige TL", on_delete=models.SET_NULL, blank=True, null=True)

    @staticmethod
    def get_active():
        return Project.objects.filter(bp=BP.get_active())

    @property
    def student_list(self):
        return ", ".join(s.name for s in self.student_set.all())

    def __str__(self):
        return f"{self.nr}: {self.title}"


class TL(models.Model):
    class Meta:
        verbose_name = "Teamleitung"
        verbose_name_plural = "Teamleitungen"
        ordering = ['bp', 'name']

    name = models.CharField(verbose_name="Name", max_length=100)
    bp = models.ForeignKey(BP, verbose_name="Zugehöriges BP", on_delete=models.CASCADE)

    @staticmethod
    def get_active():
        return TL.objects.filter(bp=BP.get_active())

    def __str__(self):
        return self.name


class Student(models.Model):
    class Meta:
        verbose_name = "Teilnehmende*r"
        verbose_name_plural = "Teilnehmende"
        ordering = ['bp', 'name']

    name = models.CharField(verbose_name="Name", max_length=100)
    bp = models.ForeignKey(BP, verbose_name="Zugehöriges BP", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Projekt")

    @staticmethod
    def get_active():
        return Student.objects.filter(bp=BP.get_active())

    def __str__(self):
        return self.name


class TLLog(models.Model):
    class Meta:
        verbose_name = "TL Log"
        verbose_name_plural = "TL Logs"
        ordering = ['-timestamp']

    bp = models.ForeignKey(BP, on_delete=models.CASCADE)
    group = models.ForeignKey(Project, on_delete=models.CASCADE)
    tl = models.ForeignKey(TL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)
    requires_attention = models.BooleanField(verbose_name="Besondere Aufmerksamkeit", blank=True, default=False,
                    help_text="Benötigt diese Gruppe aktuell besondere Aufmerksamkeit durch das Organisationsteam?")

    @property
    def simple_timestamp(self):
        return self.timestamp.strftime('%d.%m.%y %H:%M')

    def __str__(self):
        return f"{self.tl} für Gruppe {self.group.nr} am {self.simple_timestamp}"
