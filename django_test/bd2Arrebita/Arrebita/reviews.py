import datetime as dt

from .mongo import get_reviews_collection


def create_review(wine_id, wine_name, user_name, rating, comment):
    review = {
        "wine_id": str(wine_id),
        "wine_name": wine_name,
        "user_name": user_name,
        "rating": int(rating),
        "comment": comment,
        "created_at": dt.datetime.utcnow(),
    }
    get_reviews_collection().insert_one(review)


def list_reviews(wine_id=None, limit=50):
    query = {}
    if wine_id is not None:
        query["wine_id"] = str(wine_id)

    cursor = (
        get_reviews_collection()
        .find(query)
        .sort("created_at", -1)
        .limit(limit)
    )
    reviews = []
    for doc in cursor:
        doc["id"] = str(doc.get("_id"))
        rating = doc.get("rating")
        try:
            doc["rating"] = int(rating)
        except (TypeError, ValueError):
            doc["rating"] = 0
        reviews.append(doc)
    return reviews
