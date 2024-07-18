from flask import jsonify
import requests

class GoogleBooksService:
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    @staticmethod
    def get_book_details(isbn):
        url = f"{GoogleBooksService.BASE_URL}?q=isbn:{isbn}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if data["totalItems"] > 0:
                volume_info = data["items"][0]["volumeInfo"]
                authors = volume_info.get("authors", ["unknown"])
                publisher = volume_info.get("publisher", "unknown")
                published_date = volume_info.get("publishedDate", "unknown")

                return {
                    "authors": " and ".join(authors),
                    "publisher": publisher,
                    "publishedDate": published_date
                }
            else:
                return None
        else:
            return jsonify({"error": "Unable to connect to Google"}), 500