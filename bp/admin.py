from django.contrib import admin

from bp.models import BP, Project, AGGradeBeforeDeadline, AGGradeAfterDeadline, TL, Student, TLLog, TLLogProblem, TLLogReminder
from bp.models import OrgaLog
from bp.timetracking.models import TimeSpentCategory

@admin.register(BP)
class BPAdmin(admin.ModelAdmin):
    pass


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


@admin.register(TLLog)
class TLLogAdmin(admin.ModelAdmin):
    list_filter = ['bp', 'read', 'requires_attention', 'good_log']
    list_display = ['simple_timestamp', 'group', 'tl', 'requires_attention', 'bp']


@admin.register(TLLogProblem)
class TLLogProblemAdmin(admin.ModelAdmin):
    pass


@admin.register(TLLogReminder)
class TLLogReminderAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['timestamp', 'group', 'tl', 'bp']
    list_display_links = ['timestamp', 'group', 'tl']
