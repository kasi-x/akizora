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

from utils.data_io import read_dict
from utils.data_io import save_chunk
from utils.data_io import save_xhtml
from utils.logger_config import configure_logger

BOOK_DIR = Path(os.environ.get("BOOK_DIR", "/books"))
file_name_counter = Counter()


def grep_chapter_books():
    good_repos = []
    for repo_dir in list(BOOK_DIR.glob("*")):
        if repo_dir.is_dir():
            for file_path in repo_dir.glob("*"):
                if file_path.is_file() and file_path.name.startswith("chapter-1"):
                    good_repos.append(repo_dir)
                    break
    return good_repos


def get_max_nest_level(chapters):
    max_result = 0
    for chapter in chapters:
        if sub_chapters := chapter.get("subchapters"):
            max_result = max(get_max_nest_level(sub_chapters), max_result)
        else:
            max_result = max(chapter["nest_level"], max_result)
    return max_result


def grep_shallow_nested_books(repos: list[Path]):
    results = []
    for repo_dir in repos:
        chapters = read_dict(repo_dir / "toc.json")
        print(f"f{repo_dir} has {len(chapters)} chapters.")
        if not chapters:
            continue
        nest_level = get_max_nest_level(chapters)
        if 1 <= nest_level < 2:
            print(f"{repo_dir} append: {nest_level}")
            results.append(repo_dir)
        else:
            print(f"{repo_dir} has deep nest level: {nest_level}")
    return results


def main():
    configure_logger()
    logger = structlog.get_logger(__name__)
    good_repos = grep_chapter_books()
    good_repos = grep_shallow_nested_books(good_repos)
    pprint(good_repos)
    data = [str(data) for data in good_repos]
    save_chunk(data, BOOK_DIR / "easy_readable_books.json", logger)


if __name__ == "__main__":
    main()