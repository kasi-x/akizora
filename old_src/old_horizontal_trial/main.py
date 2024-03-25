import json
import re
from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Optional
from typing import Tuple

import spacy
import structlog
from logger.logger_config import configure_logger
from utils.file_operations import read_book_file
from utils.file_operations import save_to_json
from utils.text_processing import normalize_newlines
from utils.text_processing import remove_extra_spaces
from utils.text_processing import split_into_chapters


def main():
    logger.info("Start text analysis")

    normalized_text = remove_extra_spaces(normalize_newlines(read_book_file("LostHorizon.txt")))

    chapters = split_into_chapters(normalized_text)

    book_structure = Book(chapters=chapters)

    save_to_json(book_structure, "structured_output_with_dataclasses.json")


if __name__ == "__main__":
    main()
