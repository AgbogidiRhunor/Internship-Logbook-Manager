import logging
import time

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Adds Content-Security-Policy, Referrer-Policy, and
    Permissions-Policy headers to every response.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Content Security Policy
        # Allows: self, Google Fonts, Unsplash images (auth page backgrounds)
        # Blocks: inline scripts (except those with nonce), eval, object embeds
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' https://fonts.googleapis.com; "
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
    """
    Rejects requests with a body larger than MAX_UPLOAD_SIZE.
    Prevents large-body DoS attacks against non-file endpoints.
    """
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB hard ceiling

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
    """
    Logs 4xx and 5xx responses with IP, path, and method
    for anomaly detection.
    """
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
                logger.warning('RATE_LIMITED | ip=%s | user=%s | %s %s',
                               ip, username, request.method, request.path)
            elif status == 403:
                logger.warning('FORBIDDEN | ip=%s | user=%s | %s %s',
                               ip, username, request.method, request.path)
            elif status >= 500:
                logger.error('SERVER_ERROR | ip=%s | user=%s | %s %s | status=%s',
                             ip, username, request.method, request.path, status)

        return response
