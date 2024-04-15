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


def count_file_names(repo_dir: Path) -> None:
    for file_path in repo_dir.glob("*"):
        if file_path.is_file():
            file_name_counter.update([file_path.name])


def main():
    configure_logger()
    structlog.get_logger(__name__)

    for repo_dir in list(BOOK_DIR.glob("*")):
        if repo_dir.is_dir():
            count_file_names(repo_dir)
    pprint(file_name_counter)


if __name__ == "__main__":
    main()
