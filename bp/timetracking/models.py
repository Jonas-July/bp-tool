from datetime import date, timedelta

from django.db import models

class TimeInterval(models.Model):
    class Meta:
        verbose_name = "Intervall für Zeiterfassung"
        verbose_name_plural = "Intervalle für Zeiterfassung"
        ordering = ['group', 'name']

    name = models.CharField(verbose_name="Intervallname", max_length=50, blank=True)
    start = models.DateField(verbose_name="Beginn des Intervalls")
    end = models.DateField(verbose_name="Ende des Intervalls")
    group = models.ForeignKey("Project", on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Projekt")

    def is_editable_by_students(self):
        return date.today() <= self.end + timedelta(days=21)

    def __len__(self):
        length = self.end - self.start + timedelta(days=1)
        return length.days

    def __str__(self):
        return f"{self.name} der Gruppe {self.group} von {self.start} bis {self.end}"

class TimeSpentCategory(models.Model):
    class Meta:
        verbose_name = "Kategorie für Zeiterfassung"
        verbose_name_plural = "Kategorien für Zeiterfassung"

    name = models.CharField(verbose_name="Name", max_length=50)

    def __str__(self):
        return f"{self.name}"

class TimeTrackingEntry(models.Model):
    class Meta:
        verbose_name = "Eintrag für Zeiterfassung"
        verbose_name_plural = "Einträge für Zeiterfassung"

    hours = models.DecimalField(verbose_name="Stunden (h)", max_digits=5, decimal_places=2)
    category = models.ForeignKey(TimeSpentCategory, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Kategorie")
    interval = models.ForeignKey(TimeInterval, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Zeitintervall")
    student = models.ForeignKey("Student", on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Teammitglied")

    def __str__(self):
        return f"{self.interval}: Eintrag von {self.student}"
