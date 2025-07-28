import dataclasses
import sqlite3
from datetime import datetime
from typing import List, Optional

from flask import Flask, g, jsonify, request

app = Flask(__name__)
DATABASE = "reviews.db"


def get_db() -> sqlite3.Connection:
    """Return a SQLite connection from Flask's application context."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception) -> None:
    """Close the SQLite connection at the end of the request context."""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Initialize the database and create the reviews table if it does not exist."""
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


class ReviewRepository:
    """Repository that provides basic operations on reviews."""

    def __init__(self) -> None:
        self.conn = get_db()

    def insert(self, review: "Review") -> None:
        """Insert a review into the database.

        Sets the ID field of the model.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
            (review.text, review.sentiment, review.created_at),
        )
        self.conn.commit()
        review.id = cursor.lastrowid

    def fetch_all(self) -> List["Review"]:
        """Retrieve all reviews."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM reviews",
        )
        rows = cursor.fetchall()
        # Here I just imagined that db column names == model field names to make it simple
        return [Review(**dict(row)) for row in rows]

    def fetch_by_sentiment(self, sentiment: str) -> List["Review"]:
        """Retrieve all reviews with the specified sentiment."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM reviews WHERE sentiment = ?", (sentiment,))
        rows = cursor.fetchall()
        return [Review(**dict(row)) for row in rows]


class SentimentChecker:
    """Very straightforward sentiment checker."""

    POSITIVE = ["хорош", "люблю"]
    NEGATIVE = ["плохо", "ненавиж"]

    @staticmethod
    def check(text: str) -> str:
        """Analyze sentiment based on keyword matching.

        Counts mood words and then predicts result sentiment.
        """
        lowered = text.lower()
        pos_count = sum(lowered.count(p) for p in SentimentChecker.POSITIVE)
        neg_count = sum(lowered.count(n) for n in SentimentChecker.NEGATIVE)

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"


@dataclasses.dataclass
class Review:
    text: str
    sentiment: str
    created_at: str
    id: Optional[int] = None


class ReviewService:
    """A simple service to work with reviews."""

    def __init__(self) -> None:
        """Initialize the service with a ReviewRepository instance."""
        self.repo = ReviewRepository()

    def add_review(self, text: str) -> Review:
        """Add a new review with sentiment."""
        sentiment = SentimentChecker.check(text)
        review = Review(
            text=text,
            created_at=datetime.utcnow().isoformat(),
            sentiment=sentiment,
        )
        self.repo.insert(review)
        return review

    def get_reviews_by_sentiment(self, sentiment: str) -> List[Review]:
        """Get reviews filtered by sentiment.

        If sentiment is an empty string, all reviews are selected.
        If sentiment doesn't match returns empty list.
        """
        if not sentiment:
            return self.repo.fetch_all()
        return self.repo.fetch_by_sentiment(sentiment)


@app.route("/reviews", methods=["POST"])
def add_review():
    """Handle POST request to add a new review."""
    data = request.get_json()
    text = data.get("text", None)
    if not text:
        return jsonify({"error": "Field 'text' is required"}), 400

    service = ReviewService()
    review = service.add_review(text)
    return jsonify(review), 201


@app.route("/reviews", methods=["GET"])
def get_reviews():
    """Handle GET request to fetch reviews by sentiment."""
    sentiment = request.args.get("sentiment", "")
    service = ReviewService()
    reviews = service.get_reviews_by_sentiment(sentiment)
    return jsonify(reviews)


if __name__ == "__main__":
    init_db()
    app.run()
