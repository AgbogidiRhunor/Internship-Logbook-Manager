import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Sets security headers on every response.

    style-src includes 'unsafe-inline' because Django templates generate
    conditional inline styles (e.g. compliance colour coding) that cannot
    be moved to static CSS without nonces. All inline style values are
    server-generated — never from user input.

    script-src includes 'unsafe-inline' for the same reason: dashboard
    pages embed small Django-template-driven <script> blocks that pass
    server context (log counts, compliance percentages) to canvas charts.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https://images.unsplash.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        response['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=()'
        )

        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'

        return response


class RequestSizeLimitMiddleware:
    """Rejects request bodies larger than 10 MB."""

    MAX_UPLOAD_SIZE = 10 * 1024 * 1024

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length:
            try:
                if int(content_length) > self.MAX_UPLOAD_SIZE:
                    from django.http import HttpResponse
                    logger.warning(
                        'Request body too large: %s bytes from %s',
                        content_length,
                        request.META.get('REMOTE_ADDR'),
                    )
                    return HttpResponse('Request body too large.', status=413)
            except (ValueError, TypeError):
                pass
        return self.get_response(request)


class AuditLogMiddleware:
    """Logs 4xx and 5xx responses for anomaly detection."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        status = response.status_code
        if status >= 400:
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            user = getattr(request, 'user', None)
            username = user.username if (user and user.is_authenticated) else 'anonymous'
            if status == 429:
                logger.warning('RATE_LIMITED | ip=%s | user=%s | %s %s', ip, username, request.method, request.path)
            elif status == 403:
                logger.warning('FORBIDDEN | ip=%s | user=%s | %s %s', ip, username, request.method, request.path)
            elif status >= 500:
                logger.error('SERVER_ERROR | ip=%s | user=%s | %s %s | status=%s', ip, username, request.method, request.path, status)
        return response