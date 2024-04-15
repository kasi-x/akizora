import json
import os
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Self

import structlog
from lxml import etree
from lxml.etree import HTMLParser
from lxml.etree import _Element as Element
from structlog.stdlib import BoundLogger

from utils.logger_config import configure_logger

BOOK_DIR = Path(os.environ.get("BOOK_DIR", "/books"))


namespaces = {"xhtml": "http://www.w3.org/1999/xhtml"}


@dataclass
class Chapter:
    title: str
    number: str
    name: str
    href: str
    nest_level: int
    query: str
    url: str
    subchapters: list[Self | Element] = field(default_factory=list)
    """ # EXAMPLE:
    title : 'III: The Division of Labour'
    number: 'III'
    name : ': The Division of Labour'
    ## MEMO: I hate this format.

    # MEMO:nest level:
    these book nest_levl is very deep. max is 5.
    aleksandr-kuprin_short-fiction_s-koteliansky_j-m-murry_stephen-graham_rosa-savory-graham_leo-pasvols
    alexander-pushkin_eugene-onegin_henry-spalding
    adam-smith_the-wealth-of-nations
    """

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
    # ANNOTATE: In fact, return value is lxml.etree._XpathObject, but list[Element] is more useful for me. Because XpathObject is too wide like str, int, None, Element, list[Element]..etc. But if you pass correct query, the result should be list of Element.
    return find_root(xml_data).xpath(query)  # type: ignore


def find_file_title(xml_data: bytes) -> str | None:
    return parse_from_xml_data("//html/head/title", xml_data=xml_data)[0].text


def find_chapters(xml_data: bytes) -> list[Element]:
    return parse_from_xml_data("//html/body/nav[@id='toc'][1]/ol/li", xml_data)


def process_raw_chapters_into_formated(
    raw_chapters: list[Element], query: str, nest_level=0, url=""
) -> list[Chapter]:
    return [
        make_chapter(raw_chapter, query, nest_level, url, index)
        for index, raw_chapter in enumerate(raw_chapters, start=1)
    ]


def make_chapter(a_element: Element, query: str, nest_level: int, url: str, index: int) -> Chapter:
    # EXAMPLE: `<a href="text/chapter-3.xhtml"><span epub:type="z3998:roman">III</span>: The Conference</a>`.

    def get_query_result_with_check(element: Element, query: str) -> str:
        if result := element.xpath(query):
            return result[0]  # type: ignore # reason at parse_from_xml_data
        return ""

    query = query + f"[{index}]" if query else ""

    return Chapter(
        title=" ".join(
            get_query_result_with_check(a_element, "a/span/text()"),
            get_query_result_with_check(a_element, "a/text()"),
        ),
        number=get_query_result_with_check(a_element, "a/span/text()"),
        name=get_query_result_with_check(a_element, "a/text()"),
        href=get_query_result_with_check(a_element, "a/@href"),
        nest_level=nest_level,
        query=query,
        url=url,
        subchapters=[
            make_chapter(a_sub_element, query + "/ol/li", nest_level + 1, url, index)  # type: ignore
            for index, a_sub_element in enumerate(a_element.xpath("ol/li"), start=1)  # type: ignore
            if isinstance(a_element.xpath(query + "ol/li"), list)
        ],
    )


def __post_init__(self):
    self.subchapters = process_raw_chapters_into_formated(
        raw_chapters=self.subchapters,  # type: ignore
        query=self.query + "/ol/li",
        nest_level=self.nest_level + 1,
        url=self.url,
    )
    self.title = "".join(self.number + self.name)


# //section[@id='chapter-39']/@id
# //section[@id='chapter-39']/@epub:type


def create_dict_formated_chapters(chapters):
    return [chapter.to_dict() for chapter in chapters]


def create_formated_chapters(xml_data: bytes) -> list[Chapter]:
    return process_raw_chapters_into_formated(
        find_chapters(xml_data), "//html/body/nav[@id='toc'][1]/ol/li"
    )


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


def tutorial():
    title = "john-maynard-keynes_the-economic-consequences-of-the-peace"
    with open(Path(f"/home/user/dev/kasi-x/akizora/books/{title}/toc.xhtml")) as file:
        xml_data = file.read().rstrip().encode("utf-8")

    # title = find_file_title(xml_data)
    chapters = create_formated_chapters(xml_data)

    with open(Path(f"/home/user/dev/kasi-x/akizora/books/{title}/toc.json"), "w") as fp:
        json.dump([c.to_dict() for c in chapters], fp)


def process_repo(repo_dir: Path, logger: BoundLogger, force=False) -> None:
    if not (repo_dir / "toc.xhtml").exists():
        logger.warning("toc.xhtml does not exist", repo_path=repo_dir)
        return

    if (repo_dir / "toc.json").exists() and not force:
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
            process_repo(repo_dir, logger, force=True)


if __name__ == "__main__":
    main()
