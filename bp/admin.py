from django.contrib import admin

from bp.models import BP, Project, TL, Student, TLLog, TLLogProblem, TLLogReminder


@admin.register(BP)
class BPAdmin(admin.ModelAdmin):
    pass


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['nr', 'title', 'tl', 'student_list', 'bp']
    list_display_links = ['nr', 'title']


@admin.register(TL)
class TLAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['name', 'bp', 'confirmed']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['name', 'project', 'bp']


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
