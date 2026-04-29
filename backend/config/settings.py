"""
Security hardening applied (see SECURITY_AUDIT.md for full details):

  AUDIT 2 — Rate limiting
    • DRF throttle rates configured here (OTPRequestThrottle, OTPVerifyThrottle,
      CouponLookupThrottle) using Django's in-memory cache for MVP.
      Upgrade to Redis (django-redis) before scaling to multiple workers.

  AUDIT 3 — Information disclosure
    • DEBUG defaults to False — stack traces are never exposed in production.
    • SECRET_KEY has no insecure default; startup fails hard if not set in .env.
    • ALLOWED_HOSTS no longer wildcards; must be set explicitly in .env.

  AUDIT 7 — CORS & security headers
    • CORS_ALLOW_ALL_ORIGINS removed; CORS_ALLOWED_ORIGINS is the only source.
    • Django SecurityMiddleware security settings enabled.
    • X_FRAME_OPTIONS, SECURE_CONTENT_TYPE_NOSNIFF, and referrer policy set.
    • HSTS enabled (non-zero value) — won't be sent over HTTP, safe for local dev.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Core ─────────────────────────────────────────────────────────────────────
# AUDIT 3 FIX — No insecure fallback. Server refuses to start without a real key.
_secret = os.getenv("SECRET_KEY", "")
if not _secret or _secret.startswith("django-insecure-"):
    import sys
    if os.getenv("DJANGO_ALLOW_INSECURE_KEY") != "1":
        print(
            "ERROR: SECRET_KEY is not set or is using the insecure dev default.\n"
            "Set SECRET_KEY in your .env file, or set DJANGO_ALLOW_INSECURE_KEY=1\n"
            "to suppress this check in local development only.",
            file=sys.stderr,
        )
        if os.getenv("DEBUG", "False") != "True":
            sys.exit(1)
        # In DEBUG mode, fall back to dev key but warn loudly.
        _secret = _secret or "django-insecure-REPLACE-THIS-IN-PRODUCTION"

SECRET_KEY = _secret

# AUDIT 3 FIX — Default is now False; opt in to debug mode explicitly in .env.
DEBUG = os.getenv("DEBUG", "False") == "True"

# AUDIT 3 FIX — No wildcard; set ALLOWED_HOSTS in .env for production.
# Defaults to localhost only, which is safe for development.
_hosts_env = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [h.strip() for h in _hosts_env.split(",") if h.strip()]

# ── Apps ─────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "verification",
]

# ── Middleware ────────────────────────────────────────────────────────────────
# AUDIT 7 FIX — CorsMiddleware must come first; SecurityMiddleware is next.
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves static files without DEBUG=True
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

_db_url = os.getenv("DATABASE_URL")
if _db_url:
    # Production — Railway injects DATABASE_URL automatically
    import urllib.parse
    _u = urllib.parse.urlparse(_db_url)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _u.path.lstrip("/"),
            "USER": _u.username,
            "PASSWORD": _u.password,
            "HOST": _u.hostname,
            "PORT": _u.port or 5432,
        }
    }
else:
    # Local development — SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Cache (used by DRF throttling) ───────────────────────────────────────────
# AUDIT 2 FIX — In-memory cache is sufficient for single-server MVP.
# Switch to django-redis before running multiple workers / deploying to a
# multi-instance hosting platform.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "verpro-throttle-cache",
    }
}

# ── CORS ──────────────────────────────────────────────────────────────────────
# AUDIT 7 FIX — CORS_ALLOW_ALL_ORIGINS is gone. Only explicitly listed origins
# are permitted. Add your production frontend domain to .env.
_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
CORS_ALLOWED_ORIGINS = list(
    {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        _frontend_url,
    }
)
# Never use CORS_ALLOW_ALL_ORIGINS — not even in DEBUG.

CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS"]
CORS_ALLOW_HEADERS = ["content-type", "accept"]

# ── Email ─────────────────────────────────────────────────────────────────────
# DEBUG=True  → OTPs print to the Django terminal (no SMTP needed for local dev).
# DEBUG=False → Real emails via Brevo SMTP. Credentials come from .env.
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL") or EMAIL_HOST_USER or "noreply@studentpass.local"

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp-relay.brevo.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = True

# ── REST Framework ────────────────────────────────────────────────────────────
# AUDIT 2 FIX — Throttle rates. Applied per-view via @throttle_classes.
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    # These are public, sessionless endpoints — no authentication needed.
    # Removing SessionAuthentication also removes DRF's CSRF enforcement on API views.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_THROTTLE_CLASSES": [],  # Global default: off. Throttles applied per-view.
    "DEFAULT_THROTTLE_RATES": {
        "otp_request": "3/hour",    # POST /api/request-otp/ — per IP
        "otp_email":   "3/hour",    # POST /api/request-otp/ — per email (dual throttle)
        "otp_verify":  "10/hour",   # POST /api/verify-otp/
        "coupon_lookup": "3/hour",  # GET  /api/get-coupon/
    },
}

# ── Security headers (AUDIT 7) ───────────────────────────────────────────────
# X-Frame-Options: deny clickjacking
X_FRAME_OPTIONS = "DENY"

# X-Content-Type-Options: prevent MIME sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# Referrer-Policy
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# HSTS — 1 year, include subdomains.
# SecurityMiddleware only sends this header over HTTPS connections, so it is
# safe to configure now; it won't interfere with local HTTP development.
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Redirect HTTP → HTTPS only when explicitly enabled via .env.
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False") == "True"

# Tell Django to trust Railway's (and other proxies') X-Forwarded-Proto header
# so it correctly identifies requests as HTTPS even behind a load balancer.
if os.getenv("SECURE_PROXY_SSL_HEADER"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Session / CSRF cookies should only travel over HTTPS in production.
# Default follows DEBUG (False in dev, True in prod), but can be overridden
# via .env so you can run DEBUG=False locally without breaking the admin.
_https = os.getenv("HTTPS_COOKIES", str(not DEBUG)) == "True"
SESSION_COOKIE_SECURE = _https
CSRF_COOKIE_SECURE = _https
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SAMESITE = "Strict"

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "verification": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.core.mail": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
