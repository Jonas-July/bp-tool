import csv
import math
import random
from collections import Counter

from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpResponse

from bp.models import BP, Project, AGGradeBeforeDeadline, AGGradeAfterDeadline, TL, Student, TLLog, TLLogTemplate, \
    TLLogProblem, PeerGroup
from bp.models import OrgaLog
from bp.grading.models import PitchGrade, DocsGrade
from bp.timetracking.models import TimeSpentCategory, TimeInterval


class TLLogTemplateInline(admin.TabularInline):
    model = TLLogTemplate


@admin.register(BP)
class BPAdmin(admin.ModelAdmin):
    inlines = [
        TLLogTemplateInline,
    ]


@admin.register(PeerGroup)
class PeerGroupAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['nr', 'bp']
    readonly_fields = ['member_groups_as_str']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['nr', 'title', 'tl', 'student_list', 'bp']
    list_display_links = ['nr', 'title']

    def change_view(self, request, object_id, **kwargs):
        self.pk = object_id
        return self.changeform_view(request, object_id, **kwargs)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        try:
            if db_field.name == "ag_grade":
                kwargs["queryset"] = db_field.related_model.objects.filter(project=self.pk).order_by("-timestamp")
        except AttributeError:
            # No self.pk at project creation, but also no grades, so ignore
            pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(AGGradeBeforeDeadline)
class AGGradeBeforeDeadlineAdmin(admin.ModelAdmin):
    list_filter = ['project']
    list_display = ['project', 'timestamp', 'ag_points']


@admin.register(AGGradeAfterDeadline)
class AGGradeAfterDeadlineAdmin(admin.ModelAdmin):
    list_filter = ['project']
    list_display = ['project', 'timestamp', 'ag_points']


@admin.register(PitchGrade)
class PitchGradeAdmin(admin.ModelAdmin):
    list_filter = ['project']
    list_display = ['project', 'grade_points']


@admin.register(DocsGrade)
class DocsGradeAdmin(admin.ModelAdmin):
    list_filter = ['project']
    list_display = ['project', 'grade_points']


@admin.register(TL)
class TLAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['name', 'bp', 'confirmed']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['name', 'project', 'bp']


@admin.register(OrgaLog)
class OrgaLogAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['simple_timestamp', 'group', 'tl', 'bp']


@admin.register(TimeSpentCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(TimeInterval)
class TimeIntervalAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'start', 'end']
    list_filter = ['group']
    list_display_links = ['name', 'group']


@admin.register(TLLog)
class TLLogAdmin(admin.ModelAdmin):
    list_filter = ['bp', 'read', 'requires_attention']
    list_display = ['simple_timestamp', 'group', 'tl', 'requires_attention', 'bp']


@admin.register(TLLogProblem)
class TLLogProblemAdmin(admin.ModelAdmin):
    pass
