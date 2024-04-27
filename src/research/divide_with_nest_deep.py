import json
import os
import shutil
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


def grep_chapter_kind_books():
    # some book don't have chapter-1.html
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


def grep_specific_value_nested_books(repos: list[Path], target_nest_value: int):
    results = []
    for repo_dir in repos:
        print("*" * 10)
        print(f"check {repo_dir}")
        chapters = read_dict(repo_dir / "toc.json")
        # print(f"f{repo_dir} has {len(chapters)} chapters.")
        if not chapters:
            continue
        nest_level = get_max_nest_level(chapters)
        if nest_level == target_nest_value:
            print(f"{repo_dir} append: {nest_level}")
            results.append(repo_dir)
    return results


def move_files_in_directory(src_dir: Path, dst_dir: Path) -> None:
    if not src_dir.is_dir():
        msg = f"Source path '{src_dir}' is not a directory."
        raise NotADirectoryError(msg)
    dst_dir_path = dst_dir / src_dir.name
    dst_dir_path.mkdir(parents=True, exist_ok=True)

    for src_file in src_dir.iterdir():
        if src_file.is_file():
            dst_file_path = dst_dir_path / src_file.name
            shutil.copy(src_file, dst_file_path)


def divide_with_nest_deep(repos, dst_dir: Path) -> None:
    for nest in range(10):
        target_repos = grep_specific_value_nested_books(repos, nest)

        if not target_repos:
            continue
        target_dir = dst_dir / f"nest_{nest}"
        target_dir.mkdir(parents=True, exist_ok=True)

        for src_dir in target_repos:
            print(f"move {src_dir} to {target_dir}")
            move_files_in_directory(src_dir, target_dir)


def main():
    configure_logger()
    structlog.get_logger(__name__)
    chapter_books = grep_chapter_kind_books()
    chapter_book_dir = Path("/home/user/dev/kasi-x/akizora/tutorial_data/chaptered")

    divide_with_nest_deep(chapter_books, chapter_book_dir)
    all_books = {
        files for files in BOOK_DIR.glob("*") if files.is_dir() and not files.name.startswith(".")
    }
    not_chapter_books = all_books.difference(chapter_books)
    not_chapter_book_dir = Path("/home/user/dev/kasi-x/akizora/tutorial_data/unchapetr")

    divide_with_nest_deep(not_chapter_books, not_chapter_book_dir)


if __name__ == "__main__":
    main()
