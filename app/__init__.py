from flask import Flask, session, request
from werkzeug.middleware.proxy_fix import ProxyFix
import secrets

from .config import (
    SECRET_KEY, APP_NAME, CENTER_NAME, APP_ENV,
    SESSION_COOKIE_SECURE, SESSION_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_NAME, PERMANENT_SESSION_LIFETIME,
)

def create_app():
    from .seed import seed
    from .core.templates import register as register_templates
    from .routes import web
    app=Flask(__name__,template_folder='../templates',static_folder='../static')
    # Render/Railway/other reverse proxies terminate HTTPS before Flask.
    app.wsgi_app=ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.secret_key=SECRET_KEY
    app.config.update(
        APP_NAME=APP_NAME,
        CENTER_NAME=CENTER_NAME,
        SESSION_COOKIE_SECURE=SESSION_COOKIE_SECURE,
        SESSION_COOKIE_HTTPONLY=SESSION_COOKIE_HTTPONLY,
        SESSION_COOKIE_SAMESITE=SESSION_COOKIE_SAMESITE,
        SESSION_COOKIE_NAME=SESSION_COOKIE_NAME,
        PERMANENT_SESSION_LIFETIME=PERMANENT_SESSION_LIFETIME,
        SESSION_REFRESH_EACH_REQUEST=True,
        MAX_CONTENT_LENGTH=int(__import__('os').getenv('MAX_CONTENT_LENGTH', str(16 * 1024 * 1024))),
    )

    @app.after_request
    def security_headers(response):
        # Baseline browser hardening. CSP is intentionally omitted here because the
        # existing UI uses inline styles/scripts and should not break during deploy.
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
        if APP_ENV == 'production':
            response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        return response

    @app.context_processor
    def security_context():
        token=session.get('_csrf_token')
        if not token:
            token=secrets.token_urlsafe(32)
            session['_csrf_token']=token
        return {'csrf_token': token}

    register_templates(app)
    app.register_blueprint(web)
    seed()
    return app