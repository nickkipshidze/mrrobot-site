from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SOURCES = ["/source1/", "/source2/"]

EXTS_MEDIA = (".mp4", ".mp3", ".wav")
EXTS_IMAGES = (".jpg", ".jpeg", ".jfif", ".pjpeg", ".pjp", ".gif", ".png", ".svg")

SECRET_KEY = "django-insecure-v!do$^l1@o#nmk*v8ybqj-iv1&8q^pdh39ari=)hq&y%we(@)r"

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mrrobot.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["./templates"],
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

STATICFILES_DIRS = (
    "./static/",
)

STATIC_URL = "static/"

STATIC_ROOT = "./"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
