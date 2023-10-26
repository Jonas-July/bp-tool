from django.db import models

class OrgaLog(models.Model):
    class Meta:
        verbose_name = "Orga-Log"
        verbose_name_plural = "Orga-Logs"
        ordering = ['-timestamp']

    bp = models.ForeignKey("BP", on_delete=models.CASCADE)
    group = models.ForeignKey("Project", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    text = models.TextField(
        help_text="Notizen zur Gruppe"
    )
    edited = models.BooleanField(verbose_name="Bearbeitet", blank=True, default=False,
                                             help_text="Wurde der Orga-Log bearbeitet?")

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
        return OrgaLog.objects.filter(bp__active=True)

    def __str__(self):
        return f"Notiz der Orga für Gruppe {self.group.nr} am {self.simple_timestamp}"