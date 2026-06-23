import os

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
# Slowapi utilise Redis pour compter les requêtes — en tests, on utilise la mémoire
# pour éviter les ConnectionError quand Redis n'est pas disponible (CI/CD).
os.environ.setdefault("LIMITER_STORAGE_URI", "memory://")
