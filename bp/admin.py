import math
import random
from collections import Counter

from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet

from bp.models import BP, Project, AGGradeBeforeDeadline, AGGradeAfterDeadline, TL, Student, TLLog, TLLogTemplate, \
    TLLogProblem, TLLogReminder, PeerGroup
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
    readonly_fields = ['member_groups']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['nr', 'title', 'tl', 'student_list', 'bp']
    list_display_links = ['nr', 'title']
    actions = ["create_peer_groups"]

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

    @admin.action(description='In Peergruppen einteilen')
    def create_peer_groups(self, request, queryset: QuerySet):
        GROUPS_PER_PEERGROUP = settings.PEER_GROUPS_MEMBER_GROUPS_COUNT
        MAX_TRIES = settings.PEER_GROUPS_OPTIMISATION_LIMIT

        group_count = queryset.count()
        groups_to_create = math.ceil(group_count / GROUPS_PER_PEERGROUP)
        active_bp = BP.get_active()

        if PeerGroup.objects.filter(bp=active_bp).count() > 0:
            self.message_user(request, "Es existieren bereits Peergruppen, bitte zunächst löschen, um eine neue "
                                       "Einteilung vorzunehmen", messages.ERROR)
        else:
            # Create new peer groups
            for nr in range(1, groups_to_create+1):
                PeerGroup.objects.create(bp=active_bp, nr=nr)
            self.message_user(request, f"{groups_to_create} Peergruppen angelegt", messages.SUCCESS)

            # Initially assign groups to peer groups
            groups = list(queryset.all())
            random.shuffle(groups)

            dirty_groups = []
            index = 0
            peer_groups = list(PeerGroup.objects.filter(bp=active_bp))
            for pg in peer_groups:
                for i in range(GROUPS_PER_PEERGROUP):
                    if index < len(groups):
                        project: Project = groups[index]
                        project.peer_group = pg
                        project.save()
                        index += 1
                dirty_groups.append(pg)
            dirty_groups_set = set(dirty_groups)

            # Check and correct
            current_try = 0
            clean_solution = False
            while current_try < MAX_TRIES:
                dirty_groups = list(dirty_groups_set)

                current_try += 1
                if len(dirty_groups) == 0:
                    clean_solution = True
                    break

                random.shuffle(dirty_groups)
                pg = dirty_groups.pop()
                dirty_groups_set = set(dirty_groups)

                ag_counter = Counter()
                tl_counter = Counter()
                for p in pg.projects.all():
                    ag_counter[p.ag_mail] += 1
                    tl_counter[p.tl] += 1

                if len(ag_counter) == 0:
                    print(pg)

                # Check if group contains constraint violations
                # Find cases where multiple groups of the same AG or TL are in the same peer group
                most_common_ag, most_common_ag_count = ag_counter.most_common(1)[0]
                most_common_tl, most_common_tl_count = tl_counter.most_common(1)[0]
                if most_common_ag_count > 1:
                    exchange_candidate: Project = pg.projects.filter(ag_mail=most_common_ag).first()
                    print(f"Found violation (two groups of AG {most_common_ag})")
                elif most_common_tl_count > 1:
                    exchange_candidate: Project = pg.projects.filter(tl=most_common_tl).first()
                    print(f"Found violation (two groups of TL {most_common_tl})")
                else:
                    # Group is clear, no need for handling
                    continue

                # Perform the exchange
                # Get random exchange group
                other_candidate: Project = random.choice(list(BP.get_active().project_set.all()))
                other_peer_group = other_candidate.peer_group

                if pg != other_peer_group:
                    # Switch groups
                    print(f"{pg}: {exchange_candidate.peer_group} <-> {other_candidate.peer_group}")
                    exchange_candidate.peer_group = other_peer_group
                    exchange_candidate.save()
                    other_candidate.peer_group = pg
                    other_candidate.save()

                    # Mark both groups as dirty
                    dirty_groups_set.add(pg)
                    dirty_groups_set.add(other_peer_group)
                else:
                    # Unfortunately selected two candidates from the same group?
                    # Just mark as dirty again and try next time
                    dirty_groups_set.add(pg)

            if clean_solution:
                self.message_user(request, "Found solution that satisfied all constraints", messages.SUCCESS)
            else:
                self.message_user(request, f"Solution violates constraints for peer groups {', '.join(str(pg) for pg in dirty_groups_set)}", messages.WARNING)


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
