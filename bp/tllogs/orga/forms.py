import datetime
import json
import math
from collections import Counter
import random

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.db.models import QuerySet
from django.forms.utils import ErrorList

from bp.models import Project, TL, PeerGroup, BP


class LogReminderForm(forms.Form):
    tls = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)

    def send_reminders(self):
        for tl_key in self.cleaned_data["tls"]:
            tl_key = json.loads(tl_key)
            tl = TL.objects.get(pk=tl_key[0])
            if tl.user is not None and tl.user.email:
                mail = EmailMessage(
                    f"[BP TL Logs] Erinnerung: Bitte Log(s) für Projekt(e) schreiben",
                    f"Hallo {tl},\n\nfür deine Gruppe(n) {', '.join([Project.objects.get(pk=p_id).short_title_else_title for p_id in tl_key[1]])} wurde(n) seit mindestens {tl_key[2]} Tagen kein Log mehr geschrieben. Bitte trage zeitnah den aktuellen Stand im System ein.",
                    settings.SEND_MAILS_FROM,
                    [tl.user.email],
                    reply_to=[settings.SEND_MAILS_TO]
                )
                mail.send(fail_silently=False)

                for p_id in tl_key[1]:
                    project = Project.objects.get(pk=p_id)
                    project.last_reminded = datetime.datetime.now()
                    project.save()

                tl.log_reminder += 1
                tl.save()

        return f"{len(self.cleaned_data['tls'])} Erinnerungsmail(s) verschickt"

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList,
                 label_suffix=None, empty_permitted=False, field_order=None, use_required_attribute=None,
                 renderer=None):
        super().__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, field_order,
                         use_required_attribute, renderer)
        self.fields["tls"].choices = self.initial["tl_choices"]
        self.fields["tls"].initial = [k for k, _ in self.initial["tl_choices"]]


class CreatePeerGroupsForm(forms.Form):
    projects = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList,
                 label_suffix=None, empty_permitted=False, field_order=None, use_required_attribute=None,
                 renderer=None):
        super().__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, field_order,
                         use_required_attribute, renderer)
        self.fields["projects"].choices = self.initial["project_choices"]
        self.fields["projects"].initial = [k for k, _ in self.initial["project_choices"]]

    def create_peer_groups(self, request):
        GROUPS_PER_PEERGROUP = settings.PEER_GROUPS_MEMBER_GROUPS_COUNT
        MAX_TRIES = settings.PEER_GROUPS_OPTIMISATION_LIMIT

        queryset = Project.get_active().filter(pk__in=self.cleaned_data["projects"])
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
            for p in peer_group:
                ag_counter[p.ag_mail] += 1
                tl_counter[p.tl] += 1

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
            messages.add_message(request, messages.WARNING,
                                 "Es existieren bereits Peergruppen, bitte zunächst löschen, um eine neue Einteilung vorzunehmen.")
        else:
            groups = list(queryset.all())
            if groups == []:
                return

            tries = generate_peer_groups(groups, GROUPS_PER_PEERGROUP, MAX_TRIES)
            # Create new peer groups
            for nr in range(1, groups_to_create + 1):
                PeerGroup.objects.create(bp=active_bp, nr=nr)
            messages.add_message(request, messages.SUCCESS, f"{groups_to_create} Peergruppen angelegt.")

            peer_groups = list(PeerGroup.objects.filter(bp=active_bp))
            for peer, grp in zip(peer_groups, peer_groups_from_list(groups, GROUPS_PER_PEERGROUP)):
                for project in grp:
                    project.peer_group = peer
                    project.save()

            if tries < MAX_TRIES:
                messages.add_message(request, messages.SUCCESS,
                                     f"Found solution that satisfied all constraints within {tries + 1} tries")
            else:
                violated_groups = [peer for peer in peer_groups if not check_constraints(peer.projects.all())]
                messages.add_message(request, messages.WARNING,
                                     f"No solution found that satisfied all constraints within {tries} tries. "
                                     f"Solution violates constraints for peer groups {', '.join(str(pg) for pg in violated_groups)}")
