from django.db import models

class AGGrade(models.Model):
    class Meta:
        abstract = True
    project = models.ForeignKey("Project", on_delete=models.CASCADE)
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
