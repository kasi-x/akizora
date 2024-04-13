import json
import os
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Optional

import structlog
from lxml import etree
from lxml.etree import Element
from lxml.etree import HTMLParser
from structlog.stdlib import BoundLogger

from utils.logger_config import configure_logger

BOOK_DIR = Path(os.environ.get("BOOK_DIR", "/books"))


namespaces = {"xhtml": "http://www.w3.org/1999/xhtml"}


@dataclass
class Chapter:
    """input data format is like this <a href="text/chapter-3.xhtml"><span epub:type="z3998:roman">III</span>: The Conference</a>."""

    title: str
    href: str
    nest_level: int
    span: str
    query: str
    url: str
    subchapters: list["Chapter"] = field(default_factory=list)

    def __post_init__(self):
        self.subchapters = process_raw_chapters_into_formated(
            self.subchapters,
            self.nest_level + 1,
            self.url,
            self.query + "/ol/li" if self.query else "",
        )

    def to_dict(self):
        if self.subchapters:
            self.subchapters = [subchapter.to_dict() for subchapter in self.subchapters]  # type: ignore

        return asdict(self)


def find_root(xml_data: bytes) -> Element:
    # MEMO: HTMLParser is easy for me more than lxml.etree.XMLParser.
    parser = HTMLParser(encoding="UTF-8")
    # WHYNOT: if I use xml.etree.ElementTree, I can read from utf-8 string, but I don't want to do mix-usage of xml.etree.ElementTree and lxml.etree.
    return etree.fromstring(xml_data, parser)


def parse_from_xml_data(query: str, xml_data: bytes) -> list[Element]:
    return find_root(xml_data).xpath(query)


def find_file_title(xml_data: bytes) -> str | None:
    return parse_from_xml_data("//html/head/title", xml_data=xml_data)[0].text


def find_chapters(xml_data: bytes) -> list[Element]:
    return parse_from_xml_data("//html/body/nav[@id='toc'][1]/ol/li", xml_data)


def process_raw_chapters_into_formated(
    raw_chapters, nest_level=0, url="", query=None
) -> list[Chapter]:
    return [
        Chapter(
            title=raw_chapter.xpath("a/text()")[0] if raw_chapter.xpath("a/text()") else "",
            href=raw_chapter.xpath("a/@href")[0] if raw_chapter.xpath("a/@href") else "",
            # //section[@id='chapter-39']/@id
            # //section[@id='chapter-39']/@epub:type
            nest_level=nest_level,
            span=raw_chapter.xpath("a/span/text()")[0]
            if raw_chapter.xpath("a/span/text()")
            else "",
            query=query + f"[{index}]" if query else "",
            url=url,
            subchapters=raw_chapter.xpath("ol/li"),
        )
        for index, raw_chapter in enumerate(raw_chapters, start=1)
    ]


def create_dict_formated_chapters(chapters):
    return [chapter.to_dict() for chapter in chapters]


def create_formated_chapters(xml_data: bytes) -> list[Chapter]:
    return process_raw_chapters_into_formated(
        find_chapters(xml_data), query="//html/body/nav[@id='toc'][1]/ol/li"
    )


def show(element):
    # This is for debugging.
    if len(element) == 0:
        print("No elements are found.")
    if isinstance(element, list):
        print(f"{len(element)} elements are found.")
        print("{:=^30}".format(" Show Data "))
        for _i, e in enumerate(element, 1):
            print(f"{_i:=^30}")
            show(e)
    else:
        print(etree.tostring(element, pretty_print=True, encoding=str))


# from pprint import pprint
# pprint(chapters)


def tutorial():
    title = "john-maynard-keynes_the-economic-consequences-of-the-peace"
    with open(Path(f"/home/user/dev/kasi-x/akizora/books/{title}/toc.xhtml")) as file:
        xml_data = file.read().rstrip().encode("utf-8")

    # title = find_file_title(xml_data)
    chapters = create_formated_chapters(xml_data)

    with open(Path(f"/home/user/dev/kasi-x/akizora/books/{title}/toc.json"), "w") as fp:
        json.dump([c.to_dict() for c in chapters], fp)


def process_repo(repo_dir: Path, logger: BoundLogger) -> None:
    if not (repo_dir / "toc.xhtml").exists():
        logger.warning("toc.xhtml does not exist", repo_path=repo_dir)
        return

    if (repo_dir / "toc.json").exists():
        logger.info("toc.json already exists", repo_path=repo_dir)
        return

    try:
        with open(repo_dir / "toc.xhtml") as file:
            xml_data = file.read().rstrip().encode("utf-8")

        chapters = create_formated_chapters(xml_data)

        with open(repo_dir / "toc.json", "w") as fp:
            json.dump([c.to_dict() for c in chapters], fp)

        logger.info("toc.json created", repo_path=repo_dir)

    except Exception as e:
        logger.exception("Failed to process repo", repo_path=repo_dir, exception=e)


def main():
    configure_logger()
    logger = structlog.get_logger(__name__)

    for repo_dir in list(BOOK_DIR.glob("*")):
        if repo_dir.is_dir():
            process_repo(repo_dir, logger)


if __name__ == "__main__":
    main()
