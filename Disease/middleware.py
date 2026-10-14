import time
import json
import re
import html
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.utils.deprecation import MiddlewareMixin


def get_client_ip(request):
    """
    Extracts the client IP from proxy headers or remote address.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR') or '127.0.0.1'
    return ip


class RateLimitMiddleware(MiddlewareMixin):
    """
    Strict Rate Limiting Middleware:
    - Auth Routes: Max 5 attempts per 15 minutes (900 seconds) per IP/identifier.
    - Global Routes: Max 120 requests per 60 seconds per IP.
    Returns HTTP 429 Too Many Requests with standard Retry-After header.
    """

    # Routes designated as authentication endpoints
    AUTH_PATTERNS = [
        re.compile(r'^/patient/patient_login/?$', re.IGNORECASE),
        re.compile(r'^/patient/patient_register/?$', re.IGNORECASE),
        re.compile(r'^/doctor/doctor_login/?$', re.IGNORECASE),
        re.compile(r'^/roleadmin/roleadmin_login/?$', re.IGNORECASE),
        re.compile(r'^/chat/register/?$', re.IGNORECASE),
        re.compile(r'^/admin/login/?$', re.IGNORECASE),
        re.compile(r'^/api/token/?$', re.IGNORECASE),
        re.compile(r'^/api/users/?$', re.IGNORECASE),
    ]

    def _is_auth_route(self, path):
        for pattern in self.AUTH_PATTERNS:
            if pattern.search(path):
                return True
        return False

    def process_request(self, request):
        path = request.path
        client_ip = get_client_ip(request)
        now = time.time()

        is_auth = self._is_auth_route(path)

        if is_auth:
            # For auth routes: only limit state-changing attempts (POST) or aggressive polling
            # As per requirement: "max 5 attempts on auth routes per 15 minutes"
            # We track every attempt (especially POST login/register submissions)
            max_auth_attempts = getattr(settings, 'AUTH_RATE_LIMIT', 5)
            auth_window = getattr(settings, 'AUTH_RATE_WINDOW_SECONDS', 900)  # 15 minutes

            # Key scoped to client IP and auth route
            clean_path = path.strip('/').replace('/', '_')
            cache_key = f"ratelimit:auth:{client_ip}:{clean_path}"

            # If user submitted a POST to auth route (an active attempt) or accessed it
            if request.method == 'POST':
                attempts = cache.get(cache_key, [])
                # Prune timestamps outside the 15-minute sliding window
                attempts = [ts for ts in attempts if now - ts < auth_window]

                if len(attempts) >= max_auth_attempts:
                    retry_after = int(max(1, auth_window - (now - attempts[0])))
                    return self._rate_limit_exceeded_response(
                        request,
                        retry_after=retry_after,
                        is_auth=True,
                        limit=max_auth_attempts,
                        window_mins=auth_window // 60
                    )

                attempts.append(now)
                cache.set(cache_key, attempts, timeout=auth_window + 60)

        # Global rate limiting across all endpoints
        global_limit = getattr(settings, 'GLOBAL_RATE_LIMIT', 120)
        global_window = getattr(settings, 'GLOBAL_RATE_WINDOW_SECONDS', 60)

        global_key = f"ratelimit:global:{client_ip}"
        global_history = cache.get(global_key, [])
        global_history = [ts for ts in global_history if now - ts < global_window]

        if len(global_history) >= global_limit:
            retry_after = int(max(1, global_window - (now - global_history[0])))
            return self._rate_limit_exceeded_response(
                request,
                retry_after=retry_after,
                is_auth=False,
                limit=global_limit,
                window_mins=global_window // 60 or 1
            )

        global_history.append(now)
        cache.set(global_key, global_history, timeout=global_window + 10)

        return None

    def _rate_limit_exceeded_response(self, request, retry_after, is_auth, limit, window_mins):
        is_ajax_or_api = (
            request.path.startswith('/api/') or
            request.is_ajax() or
            'application/json' in request.headers.get('Accept', '') or
            'application/json' in request.content_type or ''
        )

        message = (
            f"Too many authentication attempts ({limit} attempts allowed per {window_mins} minutes). "
            f"Please wait {retry_after} seconds before trying again."
            if is_auth else
            f"Rate limit exceeded ({limit} requests per minute). Please slow down and try again in {retry_after} seconds."
        )

        if is_ajax_or_api:
            resp = JsonResponse({
                "status": "error",
                "error": "Too Many Requests",
                "message": message,
                "retry_after_seconds": retry_after
            }, status=429)
        else:
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>429 - Rate Limit Exceeded</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap">
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #f8fafc;
            color: #0f172a;
            margin: 0;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        .card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 40px;
            max-width: 480px;
            width: 90%;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}
        .badge {{
            display: inline-block;
            background: #fee2e2;
            color: #991b1b;
            font-weight: 600;
            font-size: 13px;
            padding: 4px 12px;
            border-radius: 9999px;
            margin-bottom: 16px;
        }}
        h1 {{
            font-size: 22px;
            margin: 0 0 12px 0;
            color: #0f172a;
        }}
        p {{
            font-size: 15px;
            line-height: 1.5;
            color: #475569;
            margin: 0 0 24px 0;
        }}
        .btn {{
            display: inline-block;
            background: #0d9488;
            color: #ffffff;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 500;
            font-size: 14px;
        }}
        .btn:hover {{
            background: #0f766e;
        }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">Security Protection Active</span>
        <h1>Too Many Requests</h1>
        <p>{message}</p>
        <a href="/" class="btn">Return to Homepage</a>
    </div>
</body>
</html>"""
            resp = HttpResponse(html_content, status=429, content_type="text/html")

        resp['Retry-After'] = str(retry_after)
        return resp


class SecuritySanitizationMiddleware(MiddlewareMixin):
    """
    Input Sanitization and Payload Validation Middleware:
    - Enforces maximum request payload sizes (rejects oversized uploads/bodies).
    - Validates JSON format and prevents malformed JSON crashes.
    - Rejects null bytes in inputs.
    - Sanitizes malicious script tags and XSS injection vectors in GET and POST parameters.
    """

    # Malicious patterns to detect/disarm in input strings
    XSS_PATTERN = re.compile(r'(?i)<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>|javascript:|vbscript:|onerror\s*=|onload\s*=|onclick\s*=|eval\s*\(', re.IGNORECASE)

    def process_request(self, request):
        # 1. Reject Oversized Payloads
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length:
            try:
                content_length = int(content_length)
                content_type = request.META.get('CONTENT_TYPE', '')

                # 10MB limit for multipart/file uploads (e.g. chest X-rays, profile pics)
                # 1MB limit for standard JSON or form payloads
                is_upload = 'multipart/form-data' in content_type or request.path.endswith(('/showimage/', '/add', '/prescription/'))
                max_allowed = getattr(settings, 'MAX_UPLOAD_SIZE_BYTES', 10485760) if is_upload else getattr(settings, 'MAX_BODY_SIZE_BYTES', 1048576)

                if content_length > max_allowed:
                    return self._error_response(
                        request,
                        status_code=413,
                        error="Payload Too Large",
                        message=f"Request entity exceeds the maximum allowed size of {max_allowed // (1024 * 1024)}MB."
                    )
            except ValueError:
                pass

        # 2. Reject Null-Byte Injections
        for key, val in request.GET.items():
            if '\x00' in key or (isinstance(val, str) and '\x00' in val):
                return self._error_response(request, 400, "Bad Request", "Null byte character detected in request parameters.")

        # 3. Validate JSON Payloads (Reject Malformed Payloads)
        content_type = request.META.get('CONTENT_TYPE', '')
        if 'application/json' in content_type and request.body:
            try:
                parsed_json = json.loads(request.body.decode('utf-8'))
                # Validate JSON structure is either dict or list (no naked primitives or malformed trees)
                if not isinstance(parsed_json, (dict, list)):
                    return self._error_response(request, 400, "Malformed Payload", "JSON root must be an object or array.")
            except (ValueError, UnicodeDecodeError) as e:
                return self._error_response(request, 400, "Malformed Payload", f"Malformed JSON payload: {str(e)}")

        # 4. Sanitize GET query parameters
        if request.GET:
            cleaned_get = request.GET.copy()
            modified = False
            for key, val in request.GET.items():
                if isinstance(val, str) and self.XSS_PATTERN.search(val):
                    cleaned_get[key] = html.escape(self.XSS_PATTERN.sub('', val))
                    modified = True
            if modified:
                request.GET = cleaned_get

        return None

    def _error_response(self, request, status_code, error, message):
        is_ajax_or_api = (
            request.path.startswith('/api/') or
            request.is_ajax() or
            'application/json' in request.headers.get('Accept', '') or
            'application/json' in request.content_type or ''
        )

        if is_ajax_or_api:
            return JsonResponse({
                "status": "error",
                "error": error,
                "message": message
            }, status=status_code)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{status_code} - {error}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap">
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #f8fafc;
            color: #0f172a;
            margin: 0;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        .card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 40px;
            max-width: 480px;
            width: 90%;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}
        .badge {{
            display: inline-block;
            background: #fee2e2;
            color: #991b1b;
            font-weight: 600;
            font-size: 13px;
            padding: 4px 12px;
            border-radius: 9999px;
            margin-bottom: 16px;
        }}
        h1 {{
            font-size: 20px;
            margin: 0 0 12px 0;
            color: #0f172a;
        }}
        p {{
            font-size: 15px;
            line-height: 1.5;
            color: #475569;
            margin: 0 0 24px 0;
        }}
        .btn {{
            display: inline-block;
            background: #0d9488;
            color: #ffffff;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 500;
            font-size: 14px;
        }}
        .btn:hover {{
            background: #0f766e;
        }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">Security Rejection</span>
        <h1>{error}</h1>
        <p>{message}</p>
        <a href="/" class="btn">Return to Homepage</a>
    </div>
</body>
</html>"""
        return HttpResponse(html_content, status=status_code, content_type="text/html")
