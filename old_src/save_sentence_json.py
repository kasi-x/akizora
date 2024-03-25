import json
import re
from dataclasses import dataclass
from pprint import pprint
from typing import TypedDict

import google.generativeai as genai
import structlog
from dotenv import load_dotenv
from rich.progress import BarColumn
from rich.progress import Progress
from rich.progress import TextColumn
from rich.progress import TimeRemainingColumn

from logger_config import configure_logger

load_dotenv("GOOGLE_API_KEY")

model = genai.GenerativeModel("gemini-pro")

configure_logger()
logger = structlog.get_logger()


class SentenceData(TypedDict):
    sentence: str
    tokens: int
    chapter_number: int
    section_number: int
    sentence_index: int


@dataclass
class SentenceTask:
    sentence: str
    chapter_number: int
    section_number: int
    sentence_index: int


@dataclass
class ChapterInfo:
    title: str
    chapter_number: int
    sections: list[str]


class NovelProcessor:
    def __init__(self, text: str, language: str = "en") -> None:
        self.text = text
        self.language = language
        self.chapters: list[ChapterInfo] = []
        self.processed_sentences: list[SentenceData] = []

        self.initialize_regex()

    def initialize_regex(self):
        self.chapter_split_re = re.compile(r"\n{2,}")
        self.sentence_split_re = re.compile(r"[^.!?]+[.!?]?")
        self.space_cleanup_re = re.compile(r"^\s+|\s+$")

    def split_text(self):
        chapters_content = self.chapter_split_re.split(self.text.strip())
        for chapter_number, content in enumerate(chapters_content, start=1):
            self.create_chapter(chapter_number, content)

    def create_chapter(self, chapter_number: int, content: str) -> None:
        title, *sections = content.split("\n\n", 1)
        self.chapters.append(
            ChapterInfo(
                title=title.strip(),
                chapter_number=chapter_number,
                sections=sections if sections else [""],
            ),
        )

    def clean_sentence(self, sentence: str) -> str:
        return self.space_cleanup_re.sub("", sentence).strip()

    def tokenize(self, sentence: str) -> int:
        try:
            # return int(model.count_tokens(sentence).total_tokens)
            return len(sentence)
        except Exception as e:
            logger.exception(
                "Error during tokenization",
                exception=str(e),
                sentence=sentence,
                language=self.language,
            )
            return -1

    def process_sentences(self):
        progress_columns = [
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        ]
        with Progress(*progress_columns) as progress:
            progress_task = progress.add_task("Processing...", total=len(self.chapters))
            for chapter in self.chapters:
                for section_number, section in enumerate(chapter.sections):
                    self.process_section(chapter, section_number, section)
                progress.update(progress_task, advance=1)
                progress.console.log(
                    f"Completed Chapter {chapter.chapter_number}: {chapter.title}",
                )

    def process_section(self, chapter: ChapterInfo, section_number: int, section: str) -> None:
        sentences = self.sentence_split_re.findall(section)
        for sentence_index, sentence in enumerate(sentences):
            if sentence.strip():
                self.process_and_store_sentence(chapter, section_number, sentence_index, sentence)

    def process_and_store_sentence(
        self, chapter: ChapterInfo, section_number: int, sentence_index: int, sentence: str,
    ) -> None:
        cleaned_sentence = self.clean_sentence(sentence)
        tokens = self.tokenize(cleaned_sentence)
        self.processed_sentences.append(
            SentenceData(
                sentence=cleaned_sentence,
                tokens=tokens,
                chapter_number=chapter.chapter_number,
                section_number=section_number,
                sentence_index=sentence_index,
            ),
        )

    def process(self) -> None:
        self.split_text()
        self.process_sentences()


class FileManager:
    @staticmethod
    def read_text(file_path: str) -> str:
        with open(file_path, encoding="utf-8") as file:
            return file.read()

    @staticmethod
    def save_to_json(data: list[SentenceData], file_path: str) -> None:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)


def main():
    text = FileManager.read_text("LostHorizon.txt")

    processor = NovelProcessor(text, "en")
    processor.process()

    FileManager.save_to_json(processor.processed_sentences, "processed_LostHorizon.json")

    print("Processing and saving completed.")


if __name__ == "__main__":
    main()
