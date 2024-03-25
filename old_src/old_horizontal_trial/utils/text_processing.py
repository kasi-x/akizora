import re
from dataclasses.book_structures import Chapter
from dataclasses.book_structures import Section
from dataclasses.book_structures import Sentence

import spacy
import structlog

from logger_config import configure_logger

# spaCyのモデルをロード
nlp = spacy.load("en_core_web_sm")

# Loggerの設定
configure_logger()
logger = structlog.get_logger()

newline_4_or_more_pattern = re.compile(r"\n{4,}")
newline_exactly_3_pattern = re.compile(r"\n{3}")
newline_exactly_2_pattern = re.compile(r"(?<!\n)\n\n(?!\n)")
single_newline_pattern = re.compile(r"(?<!\n)\n(?!\n)")
extra_spaces_pattern = re.compile(r"\s{2,}")


def normalize_newlines(text: str) -> str:
    text = newline_4_or_more_pattern.sub("<<ChapterBreak>>", text)
    text = newline_exactly_3_pattern.sub("<<SectionBreak>>", text)
    text = newline_exactly_2_pattern.sub("<<ParagraphBreak>>", text)
    text = single_newline_pattern.sub(" ", text)
    return extra_spaces_pattern.sub(" ", text).strip()


def is_chapter_title(line: str) -> bool:
    """行が章、プロローグ、またはエピローグの開始を示すかどうかを判断する。."""
    lower_line = line.lower()
    keywords = ["chapter", "prologue", "epilogue"]
    return any(lower_line.startswith(keyword) for keyword in keywords)


def extract_chapter_title(line: str) -> str:
    """行から章のタイトル、プロローグ、またはエピローグを抽出する。."""
    if is_chapter_title(line):
        return line.strip()
    return ""


# def split_into_chapters(text: str) -> list[Chapter]:
#     """テキストを章に分割する。."""
#     lines = text.split("\n")
#     chapters = []
#     current_chapter = None
#     current_section_text = ""
#     section_index = 1
#
#     for line in lines:
#         if is_chapter_title(line):
#             if current_chapter:
#                 # 現在のセクションを現在の章に追加
#                 if current_section_text.strip():
#                     current_chapter.sections.append(
#                         create_section(current_section_text, section_index)
#                     )
#                 chapters.append(current_chapter)
#                 section_index = 1
#                 current_section_text = ""
#             current_chapter = Chapter(
#                 chapter_number=len(chapters) + 1,
#                 chapter_title=extract_chapter_title(line),
#                 sections=[],
#             )
#         else:
#             if current_section_text:
#                 current_section_text += " "
#             current_section_text += line.strip()
#
#     # 最後の章を追加
#     if current_chapter and current_section_text.strip():
#         current_chapter.sections.append(create_section(current_section_text, section_index))
#         chapters.append(current_chapter)
#
#     return chapters
#


def create_chapter(chapter_number: int, title: str, sections: list[tuple[str, str]]) -> Chapter:
    """与えられたタイトルとセクションから章オブジェクトを作成する."""
    chapter = Chapter(chapter_number=chapter_number, chapter_title=title)
    for section_index, (_section_title, section_content) in enumerate(sections, start=1):
        section = create_section(section_content, section_index)
        chapter.sections.append(section)
    return chapter


def analyze_sections(sections_text: list[str], chapter_index: int) -> list[Section]:
    """セクションテキストを解析する。."""
    return [
        create_section(section_text, index)
        for index, section_text in enumerate(sections_text, start=1)
    ]


def create_section(section_text: str, index: int) -> Section:
    """セクションオブジェクトを作成する。."""
    sentences = analyze_sentences(section_text)
    return Section(section_number_in_chapter=index, sentences=sentences)


def analyze_sentences(section_text: str) -> list[Sentence]:
    """セクションテキストから文を解析する。."""
    doc = nlp(section_text)
    return [Sentence(text=sent.text, token_count=len(sent)) for sent in doc.sents]


def remove_extra_spaces(text: str) -> str:
    return extra_spaces_pattern.sub(" ", text).strip()


def create_sentences_from_text(text: str) -> list[Sentence]:
    """与えられたテキストから文オブジェクトのリストを生成する。."""
    doc = nlp(text)
    return [Sentence(sent.text, len(sent)) for sent in doc.sents]


def process_sections(text: str, chapter_index: int) -> list[Section]:
    """チャプターテキスト内のセクションを処理する。."""
    section_texts = split_into_sections(text)
    sections = [
        Section(section_index, create_sentences_from_text(section_text))
        for section_index, section_text in enumerate(section_texts, start=1)
    ]
    return sections


def process_chapter_text(chapter_text: str, chapter_index: int) -> Chapter:
    sections = process_sections(chapter_text, chapter_index)
    chapter_title = extract_chapter_title(chapter_text, chapter_index)
    return Chapter(chapter_index, chapter_title, sections)
