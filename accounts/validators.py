import re
from django.core.exceptions import ValidationError


def validate_matric_number(value: str):
    """Matric numbers must be alphanumeric with optional slashes and hyphens."""
    cleaned = value.strip().upper()
    if not re.match(r'^[A-Z0-9/\-]{5,30}$', cleaned):
        raise ValidationError(
            'Matric number may only contain letters, digits, slashes, and hyphens (5–30 characters).'
        )


def validate_username(value: str):
    """Usernames: 4–40 chars, letters/digits/underscores only."""
    if not re.match(r'^[a-zA-Z0-9_]{4,40}$', value.strip()):
        raise ValidationError(
            'Username must be 4–40 characters and contain only letters, digits, or underscores.'
        )


def validate_image_file(file):
    """Limit uploaded images to 5 MB and safe extensions."""
    ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    MAX_SIZE = 5 * 1024 * 1024

    if file.size > MAX_SIZE:
        raise ValidationError('Image file must be smaller than 5 MB.')

    content_type = getattr(file, 'content_type', None)
    if content_type and content_type not in ALLOWED_TYPES:
        raise ValidationError('Only JPEG, PNG, GIF, and WebP images are accepted.')
