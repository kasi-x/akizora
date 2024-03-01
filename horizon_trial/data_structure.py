from dataclasses import dataclass
from dataclasses import field


def remove_noise_space(text: str) -> str:
    return text.strip()


def count_llm_tokens(text: str) -> int:
    return len(text)


@dataclass
class Sentence:
    text: str

    def __post_init__(self):
        self.text = remove_noise_space(self.text)

    @property
    def token_count(self):
        return len(self.text.split())

    @property
    def word_count(self):
        return count_llm_tokens(self.text)

    @property
    def char_count(self):
        return len(self.text)


@dataclass
class Section:
    sentences: list[Sentence] = field(default_factory=list)

    @property
    def token_count(self):
        return sum(sentence.token_count for sentence in self.sentences)

    @property
    def word_count(self):
        return sum(sentence.word_count for sentence in self.sentences)

    @property
    def char_count(self):
        return sum(sentence.char_count for sentence in self.sentences)

    @property
    def sentences_count(self):
        return len(self.sentences)


@dataclass
class Chapter:
    chapter_title: str = "NO_TITLE"
    sections: list[Section] = field(default_factory=list)

    @property
    def token_count(self):
        return sum(section.token_count for section in self.sections)

    @property
    def word_count(self):
        return sum(section.word_count for section in self.sections)

    @property
    def char_count(self):
        return sum(section.char_count for section in self.sections)

    @property
    def sentences_count(self):
        return sum(section.sentences_count for section in self.sections)

    @property
    def sections_count(self):
        return len(self.sections)


@dataclass
class Book:
    title: str = "NO_TITLE"
    chapters: list[Chapter] = field(default_factory=list)

    @property
    def token_count(self):
        return sum(chapter.token_count for chapter in self.chapters)

    @property
    def word_count(self):
        return sum(chapter.word_count for chapter in self.chapters)

    @property
    def char_count(self):
        return sum(chapter.char_count for chapter in self.chapters)

    @property
    def sentences_count(self):
        return sum(chapter.sentences_count for chapter in self.chapters)

    @property
    def sections_count(self):
        return sum(chapter.sections_count for chapter in self.chapters)

    @property
    def chapters_count(self):
        return len(self.chapters)
