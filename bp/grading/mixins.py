from bp.models import Project


class ProjectByOrderIDMixin:
    def get_object(self, queryset=None):
        return Project.objects.get(order_id=self.kwargs["order_id"])

class ProjectGradesMixin:
    @staticmethod
    def get_grading_context_data(context, project):
        beforedeadline = project.aggradebeforedeadline_set.all().order_by("-timestamp")
        afterdeadline = project.aggradeafterdeadline_set.all().order_by("-timestamp")
        context["gradings_before"] = beforedeadline
        context["gradings_after"] = afterdeadline
        context["gradings_before_count"] = context["gradings_before"].count()
        context["gradings_after_count"] = context["gradings_after"].count()
        context["gradings_count"] = context["gradings_before_count"] + context["gradings_after_count"]
        context["valid_grade_after"] = (project.ag_grade and project.ag_grade.pk) or None
        context["valid_grade_before"] = None if (context["valid_grade_after"] or not beforedeadline.first()) \
                                        else beforedeadline.first().pk
        return context
