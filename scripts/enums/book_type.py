from enum import Enum

class BookType(str, Enum):
    EBOOK = "ebook"
    PAPERBACK = "paperback"
    HARDCOVER = "hardcover"
    AUDIOBOOK = "audiobook"
