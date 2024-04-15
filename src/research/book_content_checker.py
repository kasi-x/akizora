import json
import os
from collections import Counter
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from pprint import pprint
from typing import Self

import structlog
from lxml import etree
from lxml.etree import HTMLParser
from lxml.etree import _Element as Element
from structlog.stdlib import BoundLogger

from utils.logger_config import configure_logger

BOOK_DIR = Path(os.environ.get("BOOK_DIR", "/books"))
file_name_counter = Counter()


def main():
    configure_logger()
    structlog.get_logger(__name__)

    for repo_dir in list(BOOK_DIR.glob("*")):
        if repo_dir.is_dir():
            is_correct_repo = False
            for file_name in repo_dir.glob("*"):
                if is_correct_repo:
                    break
                if file_name.is_file() and file_name.name.startswith("chapter-1"):
                    # print(f"Repo {repo_dir} does not have a chapter-* file")
                    is_correct_repo = True
                    break
            if not is_correct_repo:
                print(f"Repo {repo_dir} doen't have a chapter-* file")
                pprint(list(repo_dir.glob("*")))


if __name__ == "__main__":
    main()


# https://standardebooks.org/ebooks/aesop/fables/v-s-vernon-jones/text/single-page
"""
Repo /home/user/dev/kasi-x/akizora/books/aleksandr-kuprin_short-fiction_s-koteliansky_j-m-murry_stephen-graham_rosa-savory-graham_leo-pasvols doesn't have a chapter-* file
# It is chunk of science fiction book and the list is small talk titles
Repo /home/user/dev/kasi-x/akizora/books/aesop_fables_v-s-vernon-jones doesn't have a chapter-* file
# It is fables book and all story in./fables.xhtml.
Repo /home/user/dev/kasi-x/akizora/books/adam-mickiewicz_pan-tadeusz_maude-ashurst-biggs doesn't have a chapter-* file
# Book1, Book2, Book3
Repo /home/user/dev/kasi-x/akizora/books/.ipynb_checkpoints doesn't have a chapter-* file
Repo /home/user/dev/kasi-x/akizora/books/agatha-christie_poirot-investigates doesn't have a chapter-* file
"""
