from django.contrib import admin

from bp.models import BP, Project, TL, Student


@admin.register(BP)
class BPAdmin(admin.ModelAdmin):
    pass


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['nr', 'title', 'bp']


@admin.register(TL)
class TLAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['name', 'bp']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['name', 'project', 'bp']
