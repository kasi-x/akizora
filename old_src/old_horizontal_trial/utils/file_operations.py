import json

import structlog

from logger_config import configure_logger

from .dataclasses.book_structures import Book
from .dataclasses.book_structures import Chapter
from .dataclasses.book_structures import Section
from .dataclasses.book_structures import Sentence

configure_logger()
logger = structlog.get_logger()


def read_book_file(file_path: str) -> str:
    """本のファイルを読み込み、テキストを返す。."""
    try:
        with open(file_path, encoding="utf-8") as file:
            return file.read()
    except OSError as e:
        logger.exception("File error", exc_info=e)
        return ""


def save_to_json(book: Book, file_path: str) -> None:
    """BookオブジェクトをJSONに保存する。."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(book, f, ensure_ascii=False, indent=4, default=lambda o: o.__dict__)
    except OSError as e:
        logger.exception("Failed to save JSON", exc_info=e)
