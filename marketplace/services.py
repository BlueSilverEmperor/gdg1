import re
import requests
import logging

logger = logging.getLogger(__name__)

OPEN_LIBRARY_API_URL = "https://openlibrary.org/api/books"


def sanitize_isbn(isbn_str: str) -> str:
    """
    Remove dashes, spaces, and clean up ISBN string.
    """
    if not isbn_str:
        return ""
    return re.sub(r'[\s\-]', '', isbn_str).upper()


def fetch_book_by_isbn(isbn: str) -> dict:
    """
    Query Open Library Books API for metadata corresponding to an ISBN.
    Returns dictionary with title, authors, cover_image_url, and publication_year.
    """
    clean_isbn = sanitize_isbn(isbn)
    if not (len(clean_isbn) == 10 or len(clean_isbn) == 13):
        return {
            'success': False,
            'error': f"Invalid ISBN length: {len(clean_isbn)}. ISBN must be 10 or 13 digits."
        }

    bibkey = f"ISBN:{clean_isbn}"
    params = {
        'bibkeys': bibkey,
        'format': 'json',
        'jscmd': 'data'
    }
    headers = {
        'User-Agent': 'CampusMarketplace/1.0 (Student Peer-to-Peer; +https://campusmarket.local)'
    }

    try:
        response = requests.get(
            OPEN_LIBRARY_API_URL,
            params=params,
            headers=headers,
            timeout=8
        )
        if response.status_code != 200:
            return {
                'success': False,
                'error': f"Open Library responded with HTTP {response.status_code}"
            }

        data = response.json()
        book_info = data.get(bibkey)
        if not book_info:
            return {
                'success': False,
                'error': f"No book records found on Open Library for ISBN {clean_isbn}."
            }

        title = book_info.get('title', 'Unknown Title')
        
        # Authors list
        authors_list = [a.get('name') for a in book_info.get('authors', []) if 'name' in a]
        authors = ", ".join(authors_list) if authors_list else "Unknown Author"

        # Cover image
        cover = book_info.get('cover', {})
        cover_url = cover.get('large') or cover.get('medium') or cover.get('small') or ""

        # Publication year
        publish_date = book_info.get('publish_date', '')
        year_match = re.search(r'\b(19\d\d|20\d\d)\b', str(publish_date))
        publication_year = year_match.group(1) if year_match else (publish_date or "Unknown")

        # Build helpful description
        description_lines = [
            f"Title: {title}",
            f"Author(s): {authors}",
            f"Publication Year: {publication_year}",
            f"ISBN: {clean_isbn}",
        ]
        if 'number_of_pages' in book_info:
            description_lines.append(f"Pages: {book_info['number_of_pages']}")

        return {
            'success': True,
            'isbn': clean_isbn,
            'title': title,
            'authors': authors,
            'cover_image_url': cover_url,
            'publication_year': publication_year,
            'suggested_description': "\n".join(description_lines)
        }

    except requests.exceptions.Timeout:
        logger.warning("Open Library lookup timed out for ISBN %s", clean_isbn)
        return {
            'success': False,
            'error': "Open Library API timed out. Please try again or fill in the details manually."
        }
    except requests.exceptions.RequestException as e:
        logger.error("Network error querying Open Library for ISBN %s: %s", clean_isbn, str(e))
        return {
            'success': False,
            'error': f"Network error during lookup: {str(e)}"
        }
    except Exception as e:
        logger.exception("Unexpected error in fetch_book_by_isbn")
        return {
            'success': False,
            'error': f"Lookup failed: {str(e)}"
        }
