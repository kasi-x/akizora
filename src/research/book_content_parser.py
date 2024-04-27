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

# from data_adapter.standard_ebook_toc import Chapter
from utils.data_io import read_dict
from utils.data_io import read_xhtml
from utils.data_io import save_chunk
from utils.data_io import save_xhtml
from utils.logger_config import configure_logger


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


# def get_content_from_xhtml(xhtml: str) -> str:
#     parser = HTMLParser()
#     tree: Element = etree.fromstring(xhtml, parser)
#     content = tree.xpath("//body")[3]
#     return etree.tostring(content, pretty_print=True).decode("utf-8")


def show(element: Element | list[Element]) -> None:
    # This is for debugging.
    if len(element) == 0:
        print("No elements are found.")
    if isinstance(element, list):
        print(f"{len(element)} elements are found.")
        print("{:=^30}".format(" Show Data "))
        for _i, e in enumerate(element, 1):
            print(f"{_i:=^30}")
            show(e)
    if isinstance(element, Element):
        print(etree.tostring(element, pretty_print=True, encoding=str))
    else:
        print("No elements are found.")


BOOK_DIR = Path("/home/user/dev/kasi-x/akizora/tutorial_data/chaptered/nest_0/")

configure_logger()
logger = structlog.get_logger(__name__)
dirs = BOOK_DIR.glob("*")
for target_book in dirs:
    toc: list[Chapter] = load_chapters_from_json(target_book / "toc.json")

print(target_book)
target_files = []
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
        case "halftitlepage":
            pass
        case _:
            target_files.append(file)
            # target_file_and_id[target_book + "/" + file.href.split("text/")[-1]] = (
            # file.href.split("text/")[-1].split("#")[-1].split(".xhtml")[0]
            # )
            # pprint(file)
            pprint(file.title)

            # read_xhtml(target_book + "/" + file.href.split("text/")[-1], logger))
result_dict = {}
for target_file in target_files:
    id = target_file.href.split("text/")[-1].split("#")[-1].split(".xhtml")[0]
    # print("=" * 40)
    # print(id)

    parser = HTMLParser()
    file_path = target_book / target_file.href.split("text/")[-1]
    xhtml = read_xhtml(file_path).encode("utf-8")
    tree = etree.fromstring(xhtml, parser)
    show(tree)
    # show(tree.xpath("//body")[0])
    etree.tostring(tree, pretty_print=True).decode("utf-8")

    # print(tree.xpath(f"//section[@id={id}"))
    print("=" * 40)
    # print(tree.xpath(f"//body/section[@id={id}]"))

    show(tree.xpath(f"//section[@id='{id}']/p"))
    for element in tree.xpath(f"//section[@id='{id}']/p"):
        for text in element.itertext():
            print(text.strip())
    print("+" * 40)
    result = []
    for element in tree.xpath(f"//section[@id='{id}']/p"):
        for text in element.itertext():
            text = text.strip()
            if len(text) == 0:
                result.append("\n")
            else:
                result.append(text)
    print(" ".join(result))
    result_dict[target_file.title] = " ".join(result)


if __name__ == "__main__":
    main()
