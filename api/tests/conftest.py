import os
import warnings

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
# Slowapi utilise Redis pour compter les requêtes — en tests, on utilise la mémoire
# pour éviter les ConnectionError quand Redis n'est pas disponible (CI/CD).
os.environ.setdefault("LIMITER_STORAGE_URI", "memory://")

# Filtre l'avertissement de starlette sur l'import de python-multipart.
warnings.filterwarnings(
    "ignore", category=PendingDeprecationWarning, module="starlette.*"
)

import pytest
from database import engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    """Session de test liée à une transaction toujours annulée en fin de test.

    Certaines fonctions testées (ex: process_pokemon) font leur propre
    session.commit() interne. Sans précaution, un test d'intégration qui
    ouvre une session normale sur DATABASE_URL persiste alors ses données
    pour de vrai — y compris en local, où DATABASE_URL pointe sur la base
    de dev partagée (pokemako_db), pas une base jetable comme en CI.
    C'est exactement ce qui a corrompu la ligne de Bulbizarre avec des URLs
    d'image factices (https://example.com/...).

    Ici, la session est liée à une connexion sur laquelle on a ouvert une
    transaction + une SAVEPOINT. Un commit() interne ne valide que la
    SAVEPOINT ; on la relance aussitôt (event after_transaction_end) pour
    que le code testé continue de voir une session utilisable. À la fin du
    test, on rollback la transaction externe : plus aucune donnée ne
    persiste, quel que soit le nombre de commits internes.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
