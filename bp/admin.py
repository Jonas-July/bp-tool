import csv
import math
import random
from collections import Counter

from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpResponse

from bp.models import BP, Project, AGGradeBeforeDeadline, AGGradeAfterDeadline, TL, Student, TLLog, TLLogTemplate, \
    TLLogProblem, TLLogReminder, PeerGroup
from bp.models import OrgaLog
from bp.grading.models import PitchGrade, DocsGrade
from bp.timetracking.models import TimeSpentCategory, TimeInterval
from bp.tllogs.models import TLLogEvaluation


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

        def peer_groups_from_list(groups: list, groups_per_peergroup):
            """
            Create virtual Peer Groups of size groups_per_peergroup from consecutive groups
            """
            yield from (groups[j:j + groups_per_peergroup] for j in range(0, len(groups), groups_per_peergroup))

        def check_constraints(peer_group):
            ag_counter = Counter()
            tl_counter = Counter()
            for peer in peer_group:
                ag_counter[peer.ag_mail] += 1
                tl_counter[peer.tl] += 1

            if len(ag_counter) == 0 or len(tl_counter) == 0:
                print(f"No AGs or no TLs in peer group: {peer_group}")

            # Check if group contains constraint violations
            # Find cases where multiple groups of the same AG or TL are in the same peer group
            most_common_ag, most_common_ag_count = ag_counter.most_common(1)[0]
            most_common_tl, most_common_tl_count = tl_counter.most_common(1)[0]
            if most_common_ag_count > 1:
                print(f"Found violation (two groups of AG {most_common_ag})")
                return False
            elif most_common_tl_count > 1:
                print(f"Found violation (two groups of TL {most_common_tl})")
                return False
            else:
                # Group is clear, no need for handling
                return True

        def is_valid_assignment(groups, groups_per_peergroup):
            for peer_group in peer_groups_from_list(groups, groups_per_peergroup):
                if not check_constraints(peer_group):
                    return False
            return True

        def generate_peer_groups(groups, groups_per_peergroup, max_tries):
            """
            Generate valid peer groups of size groups_per_peergroup from groups.
            Tries at most max_tries times to randomly find a valid group assignment.

            :param groups: groups that are to be assigned to peer groups
            :type groups: list of Project
            :param groups_per_peergroup: number of groups per peer group
            :type groups_per_peergroup: int
            :param max_tries: maximum number of tries before returning
            :type max_tries: int
            :return index of last try (0 <= try <= max_tries). try == max_tries indicates no solution found
            :type int
            """
            for current_try in range(max_tries):
                random.shuffle(groups)
                if is_valid_assignment(groups, groups_per_peergroup):
                    return current_try
            return max_tries

        if PeerGroup.objects.filter(bp=active_bp).count() > 0:
            self.message_user(request, "Es existieren bereits Peergruppen, bitte zunächst löschen, um eine neue "
                                       "Einteilung vorzunehmen", messages.ERROR)
        else:
            groups = list(queryset.all())
            if groups == []:
                return

            tries = generate_peer_groups(groups, GROUPS_PER_PEERGROUP, MAX_TRIES)
            # Create new peer groups
            for nr in range(1, groups_to_create + 1):
                PeerGroup.objects.create(bp=active_bp, nr=nr)
            self.message_user(request, f"{groups_to_create} Peergruppen angelegt", messages.SUCCESS)

            peer_groups = list(PeerGroup.objects.filter(bp=active_bp))
            for peer, grp in zip(peer_groups, peer_groups_from_list(groups, GROUPS_PER_PEERGROUP)):
                for project in grp:
                    project.peer_group = peer
                    project.save()

            if tries < MAX_TRIES:
                self.message_user(request, f"Found solution that satisfied all constraints within {tries + 1} tries",
                                  messages.SUCCESS)
            else:
                violated_groups = [peer for peer in peer_groups if not check_constraints(peer.projects.all())]
                self.message_user(request, f"No solution found that satisfied all constraints within {tries} tries. "
                                           f"Solution violates constraints for peer groups {', '.join(str(pg) for pg in violated_groups)}",
                                  messages.WARNING)


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
    actions = ["export_peer_group_csv"]

    @admin.action(description="Peergruppeneinteilung als CSV exportieren")
    def export_peer_group_csv(self, request, queryset):
        response = HttpResponse(content_type="application/json")
        response['Content-Disposition'] = "attachment; filename=peergroups.csv"
        writer = csv.writer(response)
        writer.writerow(["name", "moodle_id", "mail", "group"])
        for student in queryset.all():
            writer.writerow([
                student.name,
                student.moodle_id,
                student.mail,
                str(student.project.peer_group)
            ])

        return response


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


@admin.register(TLLogReminder)
class TLLogReminderAdmin(admin.ModelAdmin):
    list_filter = ['bp']
    list_display = ['timestamp', 'group', 'tl', 'bp']
    list_display_links = ['timestamp', 'group', 'tl']


@admin.register(TLLogEvaluation)
class TLLogReminderAdmin(admin.ModelAdmin):
    list_filter = ['bp', 'log']
    list_display = ['log', 'rater', 'rating', 'bp']
    list_display_links = ['log']

