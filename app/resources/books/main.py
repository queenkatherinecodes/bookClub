from flask import Flask, jsonify, request
from books import (
    get_books, create_book, get_book, update_book, delete_book,
    get_ratings, get_rating, add_new_rating, add_rating, update_rating, delete_rating, get_top_books
)

app = Flask(__name__)

@app.route('/books', methods=['GET', 'POST'])
def handle_books():
    if request.method == 'GET':
        query_string = request.query_string.decode('utf-8')
        return get_books(query_string)
    elif request.method == 'POST':
        if not request.is_json:
            return jsonify("Unsupported Media Type"), 415
        book_data = request.json
        new_book, status = create_book(book_data)
        if status == 201:
            book_id = new_book.json['id']
            book_title = book_data['title']
            add_new_rating(book_id, book_title)
        return new_book, status

@app.route('/books/<string:book_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_book(book_id):
    if request.method == 'GET':
        return get_book(book_id)
    elif request.method == 'PUT':
        if not request.is_json:
            return jsonify("Unsupported Media Type"), 415
        book_data = request.json
        updated_book, status = update_book(book_id, book_data)
        book_title = book_data['title']
        update_rating(book_id, book_title)
        return updated_book, status
    elif request.method == 'DELETE':
        delete_rating(book_id)
        return delete_book(book_id)

@app.route('/ratings', methods=['GET'])
def handle_ratings():
    query_string = request.query_string.decode('utf-8')
    return get_ratings(query_string)

@app.route('/ratings/<book_id>', methods=['GET'])
def handle_rating(book_id):
    rating_data = get_rating(book_id)
    if 'error' in rating_data:
        return jsonify(rating_data), rating_data['error']
    return jsonify(rating_data)

@app.route('/ratings/<book_id>/values', methods=['POST'])
def handle_add_rating(book_id):
    rating_data = request.get_json()
    result = add_rating(book_id, rating_data)
    if isinstance(result, tuple):
        # This is an error response
        return jsonify(result[0]), result[1]
    return jsonify(result)

@app.route('/top', methods=['GET'])
def handle_top_books():
    top_books = get_top_books()
    return top_books

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)