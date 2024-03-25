import re
from dataclasses import dataclass
from dataclasses import field

import spacy


# Dataclass definitions
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
    content: str = ""  # Add content field
    sections: list[Section] = field(default_factory=list)


@dataclass
class Book:
    chapters: list[Chapter] = field(default_factory=list)


# Load spaCy model
nlp = spacy.load("en_core_web_sm")


# Function to mark chapters, sections, and paragraphs
def mark_text_elements(text: str) -> str:
    text = re.sub(r"(?i)\bchapter\s+\d+", lambda m: f"<<Chapter>>{m.group(0)}", text)
    text = re.sub(r"\n{2,}", "<<ParagraphBreak>>", text)
    return text


# Function to split text into chapters
def split_into_chapters(text: str) -> list[str]:
    return re.split(r"<<Chapter>>", text)[
        1:
    ]  # Skip the first split as it's before the first chapter mark


# Function to process a single chapter text
def process_chapter_text(chapter_text: str, chapter_index: int) -> Chapter:
    title, *content = chapter_text.split("<<ParagraphBreak>>", 1)
    content = content[0] if content else ""
    return Chapter(
        chapter_number=chapter_index, chapter_title=title.strip(), content=content.strip(),
    )


# Function to save chapters to files
def save_chapters_to_files(chapters: list[Chapter]) -> None:
    for chapter in chapters:
        filename = f"chapter_{chapter.chapter_number}_{chapter.chapter_title}.txt"
        with open(filename, "w") as file:
            file.write(f"Chapter Title: {chapter.chapter_title}\n\nContent:\n{chapter.content}")


# Main processing function
def process_text_file(file_path: str) -> None:
    with open(file_path) as file:
        text = file.read()

    marked_text = mark_text_elements(text)
    chapters_texts = split_into_chapters(marked_text)
    chapters = [process_chapter_text(chap, i + 1) for i, chap in enumerate(chapters_texts)]
    print(chapters)
    save_chapters_to_files(chapters)


# Example usage
if __name__ == "__main__":
    process_text_file("sample.txt")
