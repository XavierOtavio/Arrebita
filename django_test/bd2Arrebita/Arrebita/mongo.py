from django.conf import settings

try:
    from pymongo import MongoClient
except Exception as exc:  # pragma: no cover - runtime guard
    MongoClient = None
    _import_error = exc


_client = None


def _get_client():
    global _client
    if _client is None:
        if MongoClient is None:
            raise RuntimeError(
                "pymongo is required. Install it with `pip install pymongo`."
            ) from _import_error
        _client = MongoClient(settings.MONGO_URI)
    return _client


def get_reviews_collection():
    client = _get_client()
    db = client[settings.MONGO_DB_NAME]
    return db[settings.MONGO_COLLECTION]
