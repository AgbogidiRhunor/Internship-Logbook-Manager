from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_entry_date_not_future(value):
    """Entry dates cannot be in the future — you can't log tomorrow's work."""
    if value > timezone.now().date():
        raise ValidationError('Entry date cannot be in the future.')


def validate_entry_date_is_weekday(value):
    """
    Optional soft validator: warns if entry is on a weekend.
    Not enforced strictly — some companies operate weekends.
    Kept as reference, not applied by default.
    """
    if value.weekday() >= 5:  # 5=Saturday, 6=Sunday
        raise ValidationError(
            'Entry date falls on a weekend. '
            'If your placement operates on weekends, please contact your supervisor.'
        )


def validate_work_title_length(value: str):
    if len(value.strip()) < 5:
        raise ValidationError('Work title must be at least 5 characters.')


def validate_activity_description_length(value: str):
    if len(value.strip()) < 20:
        raise ValidationError(
            'Activity description must be at least 20 characters. '
            'Please describe your work in sufficient detail.'
        )
