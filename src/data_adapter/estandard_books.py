import base64
import json
import os
import xml
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import requests
import structlog
from lxml import etree
from lxml.etree import Element
from lxml.etree import XMLParser


@dataclass
class TextComponent:
    def __init__(self, title, sections):
        self.title = title
        self.sections = sections


class SectionType(Enum):
    SECTION = "section"
    BLOCKQUOTE = "blockquote"


@dataclass
class HgroupInfo:
    ordinal: str
    title: str


@dataclass
class XhtmlSection:
    section_id: str
    epub_type: str
    hgroup_info: HgroupInfo
    paragraphs: list


def get_page_title(data_root) -> str:
    namespaces = {"xhtml": "http://www.w3.org/1999/xhtml"}
    return data_root.xpath("//xhtml:head/xhtml:title", namespaces=namespaces)[0].text


def process_blockquote(blockquote):
    """Blockquote 要素からテキストを抽出して整形します."""
    namespaces = {"xhtml": "http://www.w3.org/1999/xhtml"}

    blocks = []
    for div in blockquote.findall("xhtml:div", namespaces=namespaces):
        header_text = div.find("xhtml:header/xhtml:p", namespaces=namespaces).text
        if header_text:
            blocks.append(f"**{header_text}**")

        # 各span要素からテキストを抽出する
        paragraph = " ".join(
            span.text for span in div.findall("xhtml:p/xhtml:span", namespaces=namespaces)
        )
        blocks.append(paragraph)

    return "\n".join(blocks)


def process_hgroup(hgroup):
    namespaces = {"xhtml": "http://www.w3.org/1999/xhtml"}

    return HgroupInfo(
        ordinal=hgroup.find("xhtml:h2[@epub:type='ordinal']", namespaces=namespaces).text
        if hgroup.find("xhtml:h2[@epub:type='ordinal']", namespaces=namespaces)
        else None,
        title=hgroup.find("xhtml:p[@epub:type='title']", namespaces=namespaces).text
        if hgroup.find("xhtml:p[@epub:type='title']", namespaces=namespaces)
        else None,
    )


def process_subsection(subsection) -> SubSection:
    pass
    # sectiontype, section_id, epub_type, hgroup_info, paragraphs

    # return SubSection(


def parse_xhtml(xhtml_element: Element) -> TextComponent:
    """XHTMLデータを解析し、TextComponentインスタンスを生成します。.

    Args:
        xhtml_element: XHTMLデータ

    Returns:
        TextComponentインスタンス
    """
    namespaces = {"xhtml": "http://www.w3.org/1999/xhtml"}

    title = get_page_title(xhtml_element)

    sections = []
    for section in xhtml_element.xpath("//xhtml:body/xhtml:section", namespaces=namespaces):
        section_id = section.get("id")
        epub_type = section.get("epub:type")
        hgroup_info = HgroupInfo(
            ordinal=section.find("xhtml:h2", namespaces=namespaces).text
            if section.find("xhtml:h2", namespaces=namespaces) is not None
            else None,
            title=section.find("xhtml:p", namespaces=namespaces).text
            if section.find("xhtml:p", namespaces=namespaces) is not None
            else None,
        )

        paragraphs = []
        temporary_subsection = []

        for element in section:
            if element.tag == "{http://www.w3.org/1999/xhtml}p":
                if temporary_subsection:
                    subsection = process_subsection(temporary_subsection)
                    paragraphs.append(subsection)
                    temporary_subsection = []
                paragraphs.append(element.text)

            else:
                temporary_subsection.append(element)

        # セクション情報に追加
        # section_type = (
        #     SectionType.SECTION if epub_type != "z3998:verse" else SectionType.BLOCKQUOTE
        # )
        sections.append(Section(section_id, epub_type, hgroup_info, paragraphs))

    return TextComponent(title, sections)


def main():
    api_token = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
    title = "john-maynard-keynes_the-economic-consequences-of-the-peace"
    if Path(f"{title}.json").exists():
        with open(f"{title}.json") as fp:
            file_info_dict = json.load(fp)
    else:
        url = f"https://api.github.com/repos/standardebooks/{title}/git/trees/master:src/epub/text"
        headers = {"Authorization": "token %s" % api_token}
        file_info_dict = get_file_info(url, headers)
        with open(f"{title}.json", "w") as fp:
            json.dump(file_info_dict, fp)
    # xml_string = file_info_dict.get("chapter-1.xhtml")
    # parser = XMLParser(
    #     encoding="UTF-8", resolve_entities=False, strip_cdata=False, recover=True, ns_clean=True
    # )
    # root = ET.fromstring(xml_string, parser)
    # parse_xhtml(root)
    #
    # pretty_xml = etree.tostring(root, pretty_print=True, encoding=str)
    # print(pretty_xml)
