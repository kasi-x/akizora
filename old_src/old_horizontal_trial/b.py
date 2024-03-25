import re
from dataclasses import dataclass
from dataclasses import field

import spacy
import structlog
from logger.logger_config import configure_logger


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


# spaCyのモデルをロード
nlp = spacy.load("en_core_web_sm")

# Loggerの設定
configure_logger()
logger = structlog.get_logger()

# 正規表現パターン
CHAPTER_PATTERN = re.compile(r"\bCHAPTER\s+\d+\b")
SECTION_PATTERN = re.compile(r"\bSECTION\s+\d+\b")
newline_4_or_more_pattern = re.compile(r"\n{4,}")
newline_exactly_3_pattern = re.compile(r"\n{3}")
newline_exactly_2_pattern = re.compile(r"(?<!\n)\n\n(?!\n)")
single_newline_pattern = re.compile(r"(?<!\n)\n(?!\n)")
extra_spaces_pattern = re.compile(r"\s{2,}")


def normalize_newlines(text: str) -> str:
    """テキスト内の不要な改行やスペースを正規化する。."""
    text = newline_4_or_more_pattern.sub("<<ChapterBreak>>", text)
    text = newline_exactly_3_pattern.sub("<<SectionBreak>>", text)
    text = newline_exactly_2_pattern.sub("<<ParagraphBreak>>", text)
    text = single_newline_pattern.sub(" ", text)
    return extra_spaces_pattern.sub(" ", text).strip()


def extract_titles(text: str) -> tuple[str, str, str]:
    """テキストから章、プロローグ、エピローグのタイトルを抽出する。."""
    chapters = CHAPTER_PATTERN.split(text)[1:]
    prologue, epilogue = chapters.pop(0), chapters.pop(-1)
    return prologue.strip(), chapters, epilogue.strip()


def process_sections(section_texts: list[str]) -> list[Section]:
    """セクションテキストを解析し、セクションオブジェクトのリストを返す。."""
    sections = []
    for index, section_text in enumerate(section_texts, start=1):
        sentences = analyze_sentences(section_text)
        section = Section(section_number_in_chapter=index, sentences=sentences)
        sections.append(section)
    return sections


def analyze_sentences(section_text: str) -> list[Sentence]:
    """セクション内のテキストから文を解析し、Sentenceオブジェクトのリストを返す。."""
    doc = nlp(section_text)
    return [Sentence(text=sent.text, token_count=len(sent)) for sent in doc.sents]


def split_into_sections(text: str) -> list[str]:
    """テキストをセクションに分割してリストとして返す。."""
    return SECTION_PATTERN.split(text)[1:]


def split_into_chapters(text: str) -> list[Chapter]:
    """テキストを章に分割してリストとして返す。."""
    prologue, chapters, epilogue = extract_titles(text)
    chapters = [prologue, *chapters, epilogue]
    return [
        process_chapter_text(chapter, index) for index, chapter in enumerate(chapters, start=1)
    ]


def process_chapter_text(chapter_text: str, chapter_index: int) -> Chapter:
    """チャプターテキスト内のセクションを処理する。."""
    section_texts = split_into_sections(chapter_text)

    if not section_texts:
        # セクションが見つからない場合、章のタイトルを空文字列として扱う
        chapter_title = ""
    else:
        # 章のタイトルはセクションの最初の部分
        chapter_title = section_texts.pop(0).strip()

    sections = process_sections(section_texts)
    return Chapter(chapter_index, chapter_title, sections)


# テキストを読み込む
with open("sample.txt") as file:
    text = file.read()

# テキストを正規化する
text = normalize_newlines(text)

# テキストを章に分割して処理する
chapters = split_into_chapters(text)

# チャプターをファイルに保存する
for chapter in chapters:
    filename = f"chapter_{chapter.chapter_number}_{chapter.chapter_title}.txt"
    with open(filename, "w") as file:
        file.write(str(chapter))
