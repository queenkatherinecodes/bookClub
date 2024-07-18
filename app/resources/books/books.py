import urllib.parse
from flask import jsonify
from google_books import GoogleBooksService
import uuid
from pymongo import MongoClient

VALID_GENRES = ['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', 'Other']

client = MongoClient('mongodb://mongo:27017/')
db = client.library

def get_books(query_string):
    if not query_string:
        books = list(db.books.find({}, {'_id': False}))
        return jsonify(books), 200

    query_string = urllib.parse.unquote_plus(query_string)
    query_params = query_string.split('&')
    query_filter = {}

    for param in query_params:
        if '=' not in param:
            continue  # Skip parameters without '='
        field, value = param.split('=', 1)
        query_filter[field] = value

    books = list(db.books.find(query_filter, {'_id': False}))
    return jsonify(books), 200

def create_book(book_data):
    title = book_data.get('title')
    isbn = book_data.get('ISBN')
    genre = book_data.get('genre')

    if not title or not isbn or not genre:
        return jsonify({"error": "Missing required fields"}), 400
    existing_book = db.books.find_one({"ISBN": isbn}, {'_id': False})
    if existing_book:
        return jsonify({"error": "Book with the provided ISBN already exists"}), 422
    if not is_valid_genre(genre):
        return jsonify({"error": "Invalid Genre"}), 422

    google_books_data = GoogleBooksService.get_book_details(isbn)
    if not google_books_data:
        return jsonify({"error": "Bad request to the Google Books API"}), 400

    authors = replace_unknown(google_books_data['authors'])
    first_author = authors.split(',')[0] if ',' in authors else authors

    # Generate a unique book ID
    book_id = str(uuid.uuid4())

    book = {
        'title': title,
        'authors': authors,
        'ISBN': isbn,
        'genre': genre,
        'publisher': replace_unknown(google_books_data['publisher']),
        'publishedDate': replace_unknown(google_books_data['publishedDate']),
        'id': book_id,
    }

    db.books.insert_one(book)
    return jsonify({'id': book['id']}), 201

def get_book(book_id):
    book = db.books.find_one({"id": book_id}, {'_id': False})
    if not book:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(book), 200

def update_book(book_id, book_data):
    book = db.books.find_one({"id": book_id}, {'_id': False})
    if not book:
        return jsonify({"error": "Book not found"}), 404

    required_fields = ['title', 'authors', 'ISBN', 'genre', 'publisher', 'publishedDate']
    missing_fields = [field for field in required_fields if field not in book_data]

    if missing_fields:
        return jsonify({"error": "Missing required fields"}), 422

    if 'genre' in book_data and not is_valid_genre(book_data['genre']):
        return jsonify({"error": "Invalid genre"}), 422

    db.books.update_one({"id": book_id}, {"$set": book_data})
    return jsonify({"id": book_id}), 200

def delete_book(book_id):
    result = db.books.delete_one({"id": book_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Book not found"}), 404
    return jsonify({"id": book_id}), 200

def is_valid_genre(genre):
    return genre in VALID_GENRES

def replace_unknown(value):
    return "missing" if value == "unknown" else value

def get_ratings(query_string):
    if not query_string:
        ratings = list(db.ratings.find({}, {'_id': False}))
        return jsonify(ratings), 200

    query_string = urllib.parse.unquote_plus(query_string)
    query_filter = {}

    if '=' in query_string:
        field, value = query_string.split('=', 1)
        if field == 'id':
            query_filter['id'] = value
        else:
            return jsonify({'error': 'Invalid query parameter'}), 422

    ratings = list(db.ratings.find(query_filter, {'_id': False}))
    return jsonify(ratings), 200

def get_rating(book_id):
    rating = db.ratings.find_one({"id": book_id}, {'_id': False})
    if rating:
        return jsonify(rating), 200
    else:
        return jsonify({'error': 'Book not found'}), 404

def add_new_rating(book_id, book_title):
    new_rating = {
        'values': [],
        'average': 0,
        'title': book_title,
        'id': book_id
    }
    db.ratings.insert_one(new_rating)

def add_rating(book_id, rating_data):
    try:
        value = rating_data['value']
        if value < 1 or value > 5:
            return jsonify({'error': 'Rating value must be between 1 and 5'}), 422
    except KeyError:
        return jsonify({'error': 'Missing rating value'}), 422

    # Find the book in the books collection
    book = db.books.find_one({"id": book_id}, {'_id': False})
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    # Check if the book already exists in the ratings collection
    rating = db.ratings.find_one({"id": book_id}, {'_id': False})

    if rating:
        # Book already exists, update the values and average
        values = rating['values'] + [value]
        average = sum(values) / len(values)
        db.ratings.update_one({"id": book_id}, {"$set": {"values": values, "average": average}})
    else:
        # Book doesn't exist, create a new entry
        new_rating = {
            'values': [value],
            'average': value,
            'title': book['title'],
            'id': book_id
        }
        db.ratings.insert_one(new_rating)

    updated_rating = db.ratings.find_one({"id": book_id}, {'_id': False})
    return {'average': updated_rating['average']}

def update_rating(book_id, new_title):
    db.ratings.update_one({"id": book_id}, {"$set": {"title": new_title}})

def delete_rating(book_id):
    db.ratings.delete_one({"id": book_id})

def get_top_books():
    valid_ratings = list(db.ratings.find({"$expr": {"$gte": [{"$size": "$values"}, 3]}}, {'_id': False}))
    sorted_ratings = sorted(valid_ratings, key=lambda rating: rating['average'], reverse=True)

    top_books = []
    for rating in sorted_ratings[:3]:
        top_book = {
            'id': rating['id'],
            'title': rating['title'],
            'average': rating['average']
        }
        top_books.append(top_book)

    return jsonify(top_books)