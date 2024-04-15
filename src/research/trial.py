import json
import os
from collections import Counter
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from pprint import pprint
from typing import TYPE_CHECKING
from typing import Self

import structlog
from lxml import etree
from lxml.etree import HTMLParser
from lxml.etree import _Element as Element
from structlog.stdlib import BoundLogger

# from data_adapter.standard_ebook_toc import Chapter
from utils.data_io import read_dict
from utils.data_io import save_chunk
from utils.data_io import save_xhtml
from utils.logger_config import configure_logger

if TYPE_CHECKING:
    from scrayping.github_api import RepositoryInfo

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


@dataclass
class Chapter:
    title: str
    number: str
    name: str
    href: str
    nest_level: int
    query: str
    url: str
    subchapters: list[Self]


def from_dict(chapter_data: dict) -> Chapter:
    """辞書データから `Chapter` オブジェクトを生成します。.

    Args:
        chapter_data (dict): 辞書データ

    Returns:
        Chapter: `Chapter` オブジェクト
    """
    subchapters = []
    if "subchapters" in chapter_data:
        for subchapter_data in chapter_data["subchapters"]:
            subchapters.append(from_dict(subchapter_data))

    return Chapter(
        title=chapter_data["title"],
        number=chapter_data["number"],
        name=chapter_data["name"],
        href=chapter_data["href"],
        nest_level=chapter_data["nest_level"],
        query=chapter_data["query"],
        url=chapter_data["url"],
        subchapters=subchapters,
    )


def load_chapters_from_json(json_path: str) -> list[Chapter]:
    """保存された JSON ファイルから `Chapter` オブジェクトのリストを読み込みます。.

    Args:
        json_path (str): JSON ファイルのパス

    Returns:
        List[Chapter]: `Chapter` オブジェクトのリスト
    """
    with open(json_path) as fp:
        data = json.load(fp)

    chapters = []
    for chapter_data in data:
        chapters.append(from_dict(chapter_data))

    return chapters


def main():
    configure_logger()
    logger = structlog.get_logger(__name__)
    book_paths = read_dict(BOOK_DIR / "easy_readable_books.json", logger)
    target_book = book_paths[0]
    toc: list[Chapter] = load_chapters_from_json(target_book + "/toc.json")
    for file in toc:
        match file.title:
            case "Titlepage":
                pass
            case "Imprint":
                pass
            case "Colophon":
                pass
            case "Uncopyright":
                pass
            case _:
                print(file.title)


if __name__ == "__main__":
    main()
