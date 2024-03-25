import json
import re
from typing import TypedDict

import spacy
import structlog
from src.logger_config import configure_logger

# spaCyのモデルをロード
nlp = spacy.load("en_core_web_sm")

configure_logger()
logger = structlog.get_logger()


class SentenceInfo(TypedDict):
    text: str
    token_count: int
    chapter_number: int
    chapter_title: str
    section_number_in_chapter: int
    section_number_in_text: int
    is_chapter_title: bool


class Chapter(TypedDict):
    title: str
    number: int
    content: str


def count_tokens(sentence: str) -> int:
    """Counts the number of tokens in a sentence."""
    return len(sentence.split())


def clean_section_text(section: str) -> str:
    """Removes newline characters from a section and replaces them with spaces."""
    return section.replace("\n", " ")


def is_valid_chapter_title(text: str) -> bool:
    return text.startswith("CHAPTER") or (not text.endswith(".") and len(text) <= 20)


def extract_title_and_sections(block: str) -> tuple[str, list[str]]:
    parts = re.split(r"\n{2,}", block, 1)
    return (parts[0], parts[1:]) if len(parts) > 1 else (parts[0], [])


class TextAnalyzer:
    def __init__(self, text: str) -> None:
        self.text = text
        self.chapters: list[Chapter] = []
        self.sentences_info: list[SentenceInfo] = []
        self.current_chapter_number = 0
        self.current_section_number_in_text = 0

    def analyze_text(self) -> None:
        logger.info("Start text analysis")
        chapter_blocks = self._extract_chapter_blocks()
        self._analyze_chapter_blocks(chapter_blocks)

    def _extract_chapter_blocks(self) -> list[str]:
        return re.split(r"\n{3,}", self.text.strip())

    def _analyze_chapter_blocks(self, chapter_blocks: list[str]) -> None:
        for block in chapter_blocks:
            title, sections = extract_title_and_sections(block)
            if is_valid_chapter_title(title):
                self._increment_chapter()
                self._analyze_sections(sections, title)
            else:
                self._analyze_sections([block], "")

    def _increment_chapter(self) -> None:
        self.current_chapter_number += 1

    def _analyze_sections(self, sections: list[str], title: str) -> None:
        section_number_in_chapter = 0
        for section in sections:
            section_number_in_chapter += 1
            self._analyze_section(section, title, section_number_in_chapter)

    def _analyze_section(
        self, section: str, chapter_title: str, section_number_in_chapter: int,
    ) -> None:
        cleaned_section = clean_section_text(section)
        self._process_sentences_in_section(
            cleaned_section, chapter_title, section_number_in_chapter,
        )

    def _process_sentences_in_section(
        self, section: str, chapter_title: str, section_number_in_chapter: int,
    ) -> None:
        doc = nlp(section)
        for sent in doc.sents:
            self._store_sentence_info(sent.text, chapter_title, section_number_in_chapter)

    def _store_sentence_info(
        self, sentence: str, chapter_title: str, section_number_in_chapter: int,
    ) -> None:
        self.current_section_number_in_text += 1
        sentence_info = self._create_sentence_info(
            sentence.strip(), chapter_title, section_number_in_chapter,
        )
        self.sentences_info.append(sentence_info)

    def _create_sentence_info(
        self, sentence: str, chapter_title: str, section_number_in_chapter: int,
    ) -> SentenceInfo:
        token_count = count_tokens(sentence)
        return SentenceInfo(
            text=sentence,
            token_count=token_count,
            chapter_number=self.current_chapter_number,
            chapter_title=chapter_title,
            section_number_in_chapter=section_number_in_chapter,
            section_number_in_text=self.current_section_number_in_text,
            is_chapter_title=chapter_title == sentence,
        )

    def save_to_json(self, file_path: str) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.sentences_info, f, ensure_ascii=False, indent=4)


def main():
file_path = "LostHorizon.txt"
with open(file_path, encoding="utf-8") as file:
    text = file.read()

analyzer = TextAnalyzer(text)
analyzer.analyze_text()
analyzer.save_to_json("analyzed_text.json")


if __name__ == "__main__":
    main()
