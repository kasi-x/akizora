import xml.etree.ElementTree as ET
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from lxml.etree import XMLParser

# import structlog
# from structlog.stdlib import BoundLogger

namespaces = {"xhtml": "http://www.w3.org/1999/xhtml"}


@dataclass
class Chapter:
    title: str
    href: str
    subchapters: list["Chapter"] = field(default_factory=list)


def get_chapter_info(chapter_li):
    """章の情報 (タイトル、リンク) を取得.

    Args:
        chapter_li (lxml.etree.Element): 章 `<li>` 要素

    Returns:
        chapter_info (dict): タイトルとリンクを含む辞書
    """
    title_elements = chapter_li.xpath(".//xhtml:a/text()", namespaces=namespaces)
    title = title_elements[0] if title_elements else None
    href_elements = chapter_li.xpath(".//xhtml:a/@href", namespaces=namespaces)
    href = href_elements[0] if href_elements else None

    return {"title": title, "href": href}


def extract_chapters(toc_element):
    """再帰的にEPUB目次を解析し、ネスト構造を維持した章リストを返す.

    Args:
        toc_element (lxml.etree.Element): EPUB目次 `<nav>` 要素

    Returns:
        chapters (list): Chapter オブジェクトのリスト
    """
    chapters = []
    for chapter_li in toc_element.xpath(".//xhtml:li", namespaces=namespaces):
        chapter_info = get_chapter_info(chapter_li)

        subchapters_ol = chapter_li.xpath(".//xhtml:ol", namespaces=namespaces)
        subchapters = extract_chapters(subchapters_ol[0]) if subchapters_ol else []

        chapters.append(
            Chapter(
                title=chapter_info["title"], href=chapter_info["href"], subchapters=subchapters
            )
        )

    return chapters


title = "john-maynard-keynes_the-economic-consequences-of-the-peace"
path = Path(f"/home/user/dev/kasi-x/akizora/books/{title}/toc.xhtml")

with open(path) as file:
    xml_data = file.read().rstrip()

parser = XMLParser(
    encoding="UTF-8", resolve_entities=False, strip_cdata=False, recover=True, ns_clean=True
)
root = ET.fromstring(xml_data, parser)
toc_element = root.xpath("//xhtml:nav[1]", namespaces=namespaces)[0]

chapters = extract_chapters(toc_element)

for chapter in chapters:
    print(f"- {chapter.title}")
    for subchapter in chapter.subchapters:
        print(f"  - {subchapter.title}")
