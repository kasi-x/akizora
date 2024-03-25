import json
import re
from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Optional
from typing import Tuple

import spacy
import structlog
from src.logger_config import configure_logger

# spaCyのモデルをロード
nlp = spacy.load("en_core_web_sm")

# Loggerの設定
structlog.configure()
logger = structlog.get_logger()

# 正規表現パターンをコンパイル
newline_3_or_more_pattern = re.compile(r"\n{3,}")
newline_exactly_2_pattern = re.compile(r"(?<!\n)\n\n(?!\n)")
single_newline_pattern = re.compile(r"(?<!\n)\n(?!\n)")
extra_spaces_pattern = re.compile(r"\s{2,}")


@dataclass
class Sentence:
    text: str
    token_count: int


@dataclass
class Section:
    section_number_in_chapter: int
    sentences: list[Sentence] = field(default_factory=list)


@dataclass
class Chapter:
    chapter_number: int
    chapter_title: str
    sections: list[Section] = field(default_factory=list)


@dataclass
class Book:
    chapters: list[Chapter] = field(default_factory=list)


def normalize_newlines(text: str) -> str:
    """連続する改行を適切に調整する。."""
    text = single_newline_pattern.sub("", text)
    text = newline_exactly_2_pattern.sub("\n", text)
    text = newline_3_or_more_pattern.sub("\n\n", text)
    return text


def remove_extra_spaces(text: str) -> str:
    """余分なスペースを削除する。."""
    return extra_spaces_pattern.sub(" ", text).strip()


def read_book_file(file_path: str) -> str:
    """本のファイルを読み込み、テキストを返す。."""
    try:
        with open(file_path, encoding="utf-8") as file:
            return file.read()
    except OSError as e:
        logger.exception("File error", exc_info=e)
        return ""


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


def split_into_chapters(text: str) -> list[Chapter]:
    """テキストを章に分割する。."""
    lines = text.split("\n")
    chapters = []
    current_chapter = None
    current_section_text = ""
    section_index = 1

    for line in lines:
        if is_chapter_title(line):
            if current_chapter:
                # 現在のセクションを現在の章に追加
                if current_section_text.strip():
                    current_chapter.sections.append(
                        create_section(current_section_text, section_index),
                    )
                chapters.append(current_chapter)
                section_index = 1
                current_section_text = ""
            current_chapter = Chapter(
                chapter_number=len(chapters) + 1,
                chapter_title=extract_chapter_title(line),
                sections=[],
            )
        else:
            if current_section_text:
                current_section_text += " "
            current_section_text += line.strip()

    # 最後の章を追加
    if current_chapter and current_section_text.strip():
        current_chapter.sections.append(create_section(current_section_text, section_index))
        chapters.append(current_chapter)

    return chapters


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


def save_to_json(book: Book, file_path: str) -> None:
    """BookオブジェクトをJSONに保存する。."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(book, f, ensure_ascii=False, indent=4, default=lambda o: o.__dict__)
    except OSError as e:
        logger.exception("Failed to save JSON", exc_info=e)


def main():
    logger.info("Start text analysis")

    normalized_text = remove_extra_spaces(normalize_newlines(read_book_file("LostHorizon.txt")))

    chapters = split_into_chapters(normalized_text)

    book_structure = Book(chapters=chapters)

    save_to_json(book_structure, "structured_output_with_dataclasses.json")


if __name__ == "__main__":
    main()
