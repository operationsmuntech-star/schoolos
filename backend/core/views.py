from django.conf import settings
from django.http import FileResponse, HttpResponseNotFound, HttpResponse
from pathlib import Path
import os


def spa_index(request):
    """Serve the frontend SPA index.html for the single-entry-point app."""
    # Try multiple paths to support local dev and Railway production
    paths_to_try = [
        Path(settings.BASE_DIR) / 'frontend' / 'index.html',  # Local dev
        Path(settings.STATIC_ROOT) / 'index.html',  # Production (collected static)
        Path(settings.BASE_DIR) / 'staticfiles' / 'index.html',  # Fallback
    ]
    
    for index_path in paths_to_try:
        if index_path.exists():
            try:
                with open(index_path, 'rb') as f:
                    return FileResponse(f, content_type='text/html')
            except Exception as e:
                print(f"Error serving {index_path}: {e}")
                continue
    
    # If no file found, return a simple error response
    return HttpResponse(
        '<h1>Not Found</h1><p>Frontend index.html not found. Paths tried: ' + 
        ', '.join(str(p) for p in paths_to_try) + '</p>',
        status=404,
        content_type='text/html'
    )
