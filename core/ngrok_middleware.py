"""Ngrok middleware

This middleware normalizes forwarded headers sent by tunnels (ngrok)
so Django's CSRF and Sites logic works correctly when using a tunnel.

It is intentionally conservative and only overrides host/scheme when
explicit forwarded headers are present.
"""

from urllib.parse import urlsplit


class NgrokMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        meta = request.META

        # Prefer explicit X-Forwarded headers if present
        forwarded_host = meta.get('HTTP_X_FORWARDED_HOST') or meta.get('HTTP_X_ORIGINAL_HOST')
        forwarded_proto = meta.get('HTTP_X_FORWARDED_PROTO') or meta.get('HTTP_X_ORIGINAL_PROTO')

        # Some tunnels set X-Original-URL or X-Original-Host
        original_url = meta.get('HTTP_X_ORIGINAL_URL') or meta.get('HTTP_X_ORIGINAL_URI')

        if forwarded_host:
            # Set the HOST header used by Django
            meta['HTTP_HOST'] = forwarded_host

        if forwarded_proto:
            # Update wsgi.url_scheme so request.scheme is correct
            meta['wsgi.url_scheme'] = forwarded_proto

        if original_url and 'HTTP_REFERER' not in meta:
            # If original full URL is provided, set referer for CSRF checks
            try:
                parsed = urlsplit(original_url)
                if parsed.scheme and parsed.netloc:
                    meta['HTTP_REFERER'] = f"{parsed.scheme}://{parsed.netloc}/"
            except Exception:
                pass

        # Keep existing referer when provided, but allow ngrok/localhost
        referer = meta.get('HTTP_REFERER', '')
        if referer and ('ngrok.io' in referer or 'ngrok-free.dev' in referer or 'localhost' in referer):
            meta['HTTP_REFERER'] = referer

        response = self.get_response(request)
        return response
