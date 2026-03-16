"""
accounts/templatetags/role_tags.py
Custom template tags and filters for role-based template logic.

Usage:
  {% load role_tags %}
  {% if request.user|is_student %}...{% endif %}
  {% if request.user|is_lecturer %}...{% endif %}
  {% if request.user|is_admin %}...{% endif %}
  {{ score|letter_grade }}
  {{ days|progress_bar:total }}
"""
from django import template
from django.utils.html import format_html

register = template.Library()


# ── Role filters ──────────────────────────────────────────────────

@register.filter(name='is_student')
def is_student(user):
    return getattr(user, 'is_student', False)


@register.filter(name='is_lecturer')
def is_lecturer(user):
    return getattr(user, 'is_lecturer', False)


@register.filter(name='is_admin')
def is_admin(user):
    return getattr(user, 'is_admin', False)


@register.filter(name='can_access')
def can_access(user):
    return getattr(user, 'can_access', False)


# ── Grade display ─────────────────────────────────────────────────

@register.filter(name='letter_grade')
def letter_grade(score):
    """Return letter grade string from numeric score."""
    try:
        score = int(score)
    except (ValueError, TypeError):
        return '—'
    if score >= 70: return 'A'
    if score >= 60: return 'B'
    if score >= 50: return 'C'
    if score >= 45: return 'D'
    if score >= 40: return 'E'
    return 'F'


@register.filter(name='grade_css_class')
def grade_css_class(letter):
    """Return CSS class for a letter grade."""
    mapping = {
        'A': 'grade-A', 'B': 'grade-B', 'C': 'grade-C',
        'D': 'grade-D', 'E': 'grade-E', 'F': 'grade-F',
    }
    return mapping.get(str(letter).upper(), '')


# ── Progress ──────────────────────────────────────────────────────

@register.simple_tag
def progress_percentage(logged, total):
    """Return progress percentage clamped to 0–100."""
    try:
        pct = int((int(logged) / int(total)) * 100)
        return max(0, min(100, pct))
    except (ZeroDivisionError, TypeError, ValueError):
        return 0


# ── Formatting ────────────────────────────────────────────────────

@register.filter(name='matric_display')
def matric_display(matric_number):
    """Format matric number for display — uppercase."""
    return str(matric_number).upper()


@register.inclusion_tag('partials/grading_badge.html')
def grading_badge(student_profile):
    """Render a graded/not-graded badge for a student."""
    is_graded = getattr(student_profile, 'is_graded', False)
    grade = getattr(student_profile, 'grade_record', None)
    return {
        'is_graded': is_graded,
        'grade': grade,
    }
