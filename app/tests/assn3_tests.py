import pytest
import requests
import json
import os

BASE_URL = "http://localhost:5001"

@pytest.fixture
def book_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, 'book_data.json')
    
    with open(json_file_path, 'r') as file:
        return json.load(file)

def test_post_three_books(book_data):
    ids = set()
    for book_key in ["book1", "book2", "book3"]:
        response = requests.post(f"{BASE_URL}/books", json=book_data[book_key])
        
        # Print response details for debugging
        print(f"Response for {book_key}: Status {response.status_code}, Content: {response.text}")
        
        # Check status code
        assert response.status_code == 201, f"POST request for {book_key} failed. Expected status 201, got {response.status_code}"
        
        # Parse response JSON
        try:
            response_data = response.json()
        except ValueError:
            pytest.fail(f"Invalid JSON response for {book_key}: {response.text}")
        
        # Check for ID in response
        assert 'id' in response_data, f"Response for {book_key} does not contain an 'id' field"
        
        # Add ID to set
        ids.add(response_data['id'])

    # Check for 3 unique IDs
    assert len(ids) == 3, f"Expected 3 unique IDs, but got {len(ids)}"

    print("All three books posted successfully with unique IDs")

def test_get_book1(book_data):
    # First, get all books to find the ID of "Adventures of Huckleberry Finn"
    all_books_response = requests.get(f"{BASE_URL}/books")
    assert all_books_response.status_code == 200, f"Failed to get all books. Status: {all_books_response.status_code}"
    
    all_books = all_books_response.json()
    book1 = next((book for book in all_books if book['ISBN'] == book_data['book1']['ISBN']), None)
    
    assert book1 is not None, f"Book 'Adventures of Huckleberry Finn' not found in the database"
    book_id = book1['id']

    # Now execute GET request with the retrieved ID
    response = requests.get(f"{BASE_URL}/books/{book_id}")
    
    # Print response for debugging
    print(f"GET Response: Status {response.status_code}, Content: {response.text}")
    
    # Check status code
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"
    
    # Parse JSON response
    try:
        book_data = response.json()
    except ValueError:
        pytest.fail(f"Invalid JSON response: {response.text}")
    
    # Check authors field
    assert 'authors' in book_data, "Response does not contain 'authors' field"
    assert book_data['authors'] == "Mark Twain", f"Expected author 'Mark Twain', got '{book_data['authors']}'"

    print("Successfully retrieved book1 with correct author and status code")

def test_get_all_books():
    # Execute GET request to /books
    response = requests.get(f"{BASE_URL}/books")
    
    # Print response for debugging
    print(f"GET Response: Status {response.status_code}, Content: {response.text}")
    
    # Check status code
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"
    
    # Parse JSON response
    try:
        books_data = response.json()
    except ValueError:
        pytest.fail(f"Invalid JSON response: {response.text}")
    
    # Check that the response is a list
    assert isinstance(books_data, list), f"Expected a list of books, but got {type(books_data)}"
    
    # Check that there are exactly 3 books
    assert len(books_data) == 3, f"Expected 3 books, but got {len(books_data)}"
    
    # Optionally, you can add more specific checks for each book
    for book in books_data:
        assert isinstance(book, dict), f"Expected each book to be a dictionary, but got {type(book)}"
        assert 'id' in book, "Each book should have an 'id' field"
        assert 'title' in book, "Each book should have a 'title' field"
        assert 'ISBN' in book, "Each book should have an 'ISBN' field"
        assert 'genre' in book, "Each book should have a 'genre' field"

    print("Successfully retrieved 3 books with correct status code")

def test_post_invalid_book(book_data):
    # Execute POST request with book4 data
    response = requests.post(f"{BASE_URL}/books", json=book_data["book4"])
    
    # Print response for debugging
    print(f"POST Response: Status {response.status_code}, Content: {response.text}")
    
    # Check status code is either 400 or 500
    assert response.status_code in [400, 500], f"Expected status code 400 or 500, but got {response.status_code}"
    
    # Optionally, you can check the response content for an error message
    try:
        error_data = response.json()
        assert "error" in error_data, "Response should contain an 'error' field"
        print(f"Error message: {error_data['error']}")
    except ValueError:
        print("Response is not JSON. This is acceptable if status code is 500.")
    
    print(f"Successfully received expected error status code ({response.status_code}) for invalid book")

def test_delete_book2(book_data):
    global book2_id
    # First, get all books to find the ID of "The Best of Isaac Asimov"
    all_books_response = requests.get(f"{BASE_URL}/books")
    assert all_books_response.status_code == 200, f"Failed to get all books. Status: {all_books_response.status_code}"
    
    all_books = all_books_response.json()
    book2 = next((book for book in all_books if book['ISBN'] == book_data['book2']['ISBN']), None)
    
    assert book2 is not None, f"Book 'The Best of Isaac Asimov' not found in the database"
    book2_id = book2['id']

    # Now perform the DELETE request
    delete_response = requests.delete(f"{BASE_URL}/books/{book2_id}")
    
    # Print response for debugging
    print(f"DELETE Response: Status {delete_response.status_code}, Content: {delete_response.text}")
    
    # Check status code
    assert delete_response.status_code == 200, f"Expected status code 200, but got {delete_response.status_code}"

    print(f"Successfully deleted book2 'The Best of Isaac Asimov' with ID {book2_id}")

def test_get_deleted_book2():
    global book2_id
    assert book2_id is not None, "book2_id is not set. Make sure test_delete_book2 runs before this test."

    # Perform the GET request for the deleted book
    get_response = requests.get(f"{BASE_URL}/books/{book2_id}")
    
    # Print response for debugging
    print(f"GET Response: Status {get_response.status_code}, Content: {get_response.text}")
    
    # Check status code is 404
    assert get_response.status_code == 404, f"Expected status code 404, but got {get_response.status_code}"

    print(f"Successfully verified that deleted book2 'The Best of Isaac Asimov' returns 404 when requested")

def test_post_book_with_invalid_genre(book_data):
    # Execute POST request with book5 data
    response = requests.post(f"{BASE_URL}/books", json=book_data["book5"])
    
    # Print response for debugging
    print(f"POST Response: Status {response.status_code}, Content: {response.text}")
    
    # Check status code is 422
    assert response.status_code == 422, f"Expected status code 422, but got {response.status_code}"
    
    # Check the response content for an error message
    try:
        error_data = response.json()
        assert "error" in error_data, "Response should contain an 'error' field"
        print(f"Error message: {error_data['error']}")
        
        # Optionally, check for a specific error message
        expected_error = "Invalid Genre"
        assert error_data["error"] == expected_error, f"Expected error message '{expected_error}', but got '{error_data['error']}'"
    except ValueError:
        pytest.fail("Response should be a valid JSON")
    
    print("Successfully received 422 status code for book with invalid genre")

def test_cleanup():
    # Get all books
    response = requests.get(f"{BASE_URL}/books")
    assert response.status_code == 200, f"Failed to get books. Status: {response.status_code}"
    
    books = response.json()
    
    # Delete each book
    for book in books:
        book_id = book['id']
        delete_response = requests.delete(f"{BASE_URL}/books/{book_id}")
        assert delete_response.status_code == 200, f"Failed to delete book {book_id}. Status: {delete_response.status_code}"
    
    # Verify that all books are deleted
    final_response = requests.get(f"{BASE_URL}/books")
    assert final_response.status_code == 200, f"Failed to get books after deletion. Status: {final_response.status_code}"
    assert len(final_response.json()) == 0, "Not all books were deleted"

    print("Successfully cleaned up the database by deleting all books")