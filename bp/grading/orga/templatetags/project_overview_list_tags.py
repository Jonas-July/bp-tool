from bp.templatetags.tags_project_overview_list import ProjectOverviewColumnTags

grade_column = ProjectOverviewColumnTags(priority=7 * 128)


@grade_column.register_description('bp/grading/orga/project_overview_list_column_grade_desc.html')
def grade_column_description(**kwargs):
    return {}


@grade_column.register_content('bp/grading/orga/project_overview_list_column_grade_content.html')
def grade_column_content(project, **kwargs):
    return {'pitch': project.pitch_grade_points,
            'ag': project.ag_grade_points,
            'docs': project.docs_grade_points,
            'total': project.total_points,
            'grade': calculate_grade(project.total_points) if project.grade_complete else 0,
            'div_id': f"div_{project.pk}",
            'grade_is_close_to_higher_grade': project.grade_complete and project.total_points > 100 and project.total_points % 10 > (
                    10 - 2),
            }


def calculate_grade(points):
    points = round(points, 0) - round(points, 0) % 10
    if points < 100:
        grade = 5.0
    else:
        grades = {
            100: 4.0,
            110: 3.7,
            120: 3.3,
            130: 3.0,
            140: 2.7,
            150: 2.3,
            160: 2.0,
            170: 1.7,
            180: 1.3,
            190: 1.0
        }
        grade = grades[points]
    return grade
