import re
import struct
from django.core.exceptions import ValidationError

_MAX_SIZE = 5 * 1024 * 1024


def validate_matric_number(value: str):
    cleaned = value.strip().upper()
    if not re.match(r'^[A-Z0-9/\-]{5,30}$', cleaned):
        raise ValidationError(
            'Matric number may only contain letters, digits, slashes, and hyphens (5-30 characters).'
        )


def validate_username(value: str):
    if not re.match(r'^[a-zA-Z0-9_]{4,40}$', value.strip()):
        raise ValidationError(
            'Username must be 4-40 characters and contain only letters, digits, or underscores.'
        )


def _detect_image_magic(header: bytes) -> str | None:
    if header[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if header[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if header[:6] in (b'GIF87a', b'GIF89a'):
        return 'image/gif'
    if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return 'image/webp'
    return None


def validate_image_file(file):
    if file.size > _MAX_SIZE:
        raise ValidationError('Image file must be smaller than 5 MB.')

    file.seek(0)
    header = file.read(12)
    file.seek(0)

    detected = _detect_image_magic(header)
    if detected is None:
        raise ValidationError(
            'File does not appear to be a valid image. Only JPEG, PNG, GIF, and WebP are accepted.'
        )

    # Secondary validation — open with Pillow to confirm the file is not corrupt
    # and truly decodable as an image (prevents polyglot files)
    try:
        from PIL import Image
        file.seek(0)
        img = Image.open(file)
        img.verify()
        file.seek(0)
    except Exception:
        file.seek(0)
        raise ValidationError('Image file is corrupt or cannot be decoded.')

    content_type = getattr(file, 'content_type', None)
    allowed = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    if content_type and content_type not in allowed:
        raise ValidationError('Only JPEG, PNG, GIF, and WebP images are accepted.')
