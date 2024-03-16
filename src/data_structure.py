from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Union

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv("GOOGLE_API_KEY")

model = genai.GenerativeModel("gemini-pro")
# genai.configure(api_key=GOOGLE_API_KEY)


def count_llm_tokens(text: str) -> int:
    if text == "":
        return 0
    return model.count_tokens(text).total_tokens


def remove_noise_space(text: str) -> str:
    return text.strip()
    # NOTE: I didn't know which one is better, so I commented out the code. In some case the latter can be better.
    # return re.sub(r"(?<!\n)\n(?!\n)", " ", text)


@dataclass
class Translator:
    input_token_border: int
    output_token_limit: int
    en_to_jp: float
    jp_to_en: float

    def is_able_translate_all_words(
        self,
        input_token_count: int,
        *,
        output_token_count=None,
        input_language="en",
        target_language="jp",
    ) -> bool:
        if input_token_count > self.input_token_border:
            return False
        if output_token_count is not None and output_token_count > self.output_token_limit:
            return False
        if output_token_count is None and input_language == "en" and target_language == "jp":
            output_token_count = input_token_count * self.en_to_jp
            return self.is_able_translate_all_words(
                input_token_count,
                output_token_count=output_token_count,
                input_language=input_language,
                target_language=target_language,
            )
        return input_token_count <= 10000


@dataclass
class GEMINI_PRO(Translator):
    def __init__(self):
        super().__init__(
            input_token_border=30720, output_token_limit=2048, en_to_jp=4, jp_to_en=0.25
        )


@dataclass
class GPT(Translator):
    def __init__(self):
        pass


def translate_text(base_text: str, language: str, context=None) -> str:
    def append_context(language, target_content, wide_contents) -> str:
        text = f"""
        I give you novel's context.
        === {wide_contents} ===
        In the following sentence, please translate only the next content inside '<>' into {language}.
        <{target_content}>"""
        return text

    if context:
        base_text = append_context(language, base_text, context)
    response = model.generate_content(base_text, stream=False)
    result = ""
    for chunk in response:
        result += chunk.text
    return result


def translate_all(self):
    pass


# @dataclass
# class Sentence:
# HOLD: Not Implement 'Sentence' dataclass.
# We might suffice with the use of the `Line` class instead. Creating sentences by splitting text on periods('.') can be problematic, as shown by this sentence. Ideally, sentences should be treated as atomic pieces of information, but we may not need to explicitly generate them.


@dataclass
class TextComponent:
    _title: str = field(default="")
    contents: list[Union["TextComponent", "Line"]] = field(default_factory=list)
    kind = "Base text componententent"

    def __iter__(self) -> Iterable:
        return iter(self.contents)

    @property
    def show_conets(self):
        return [content.show_conets for content in self.contents]

    @property
    def show_conets_with_title(self):
        result = ""
        for content in self.contents:
            if content.title:
                result += f"-----{content.kind} : {content.title}-----\n\n"
            result += content.show_conets_with_title + "\n"

        return result

    def __str__(self):
        result = ""
        for content in self.contents:
            if content.title:
                result += f"-----{content.kind} : {content.title}-----\n\n"
            result += content.show_conets_with_title + "\n"

        return result

    @property
    def title(self):
        return self._title if self._title else "NO_TITLE"

    @property
    def call_titles(self):
        return self._title

    @property
    def token_count(self) -> int:
        return sum(content.token_count for content in self.contents)

    @property
    def char_count(self) -> int:
        return sum(content.char_count for content in self.contents)

    @property
    def word_count(self) -> int:
        return sum(content.word_count for content in self.contents)

    @property
    def line_count(self) -> int:
        return sum(content.line_count for content in self.contents)

    @property
    def paragraph_count(self) -> int:
        return sum(1 for content in self.contents if isinstance(content, Paragraph))

    @property
    def section_count(self) -> int:
        return sum(1 for content in self.contents if isinstance(content, Section))

    @property
    def chapter_count(self) -> int:
        return sum(1 for content in self.contents if isinstance(content, Chapter))

    def __len__(self) -> int:
        return len(self.contents)

    def translate(self, language="jp", context=None) -> None:
        if self.token_count > 10000 or context:
            for content in self.contents:
                content.translate(language, context)
        if 500 < self.token_count <= 20000:
            for content in self.contents:
                content.translate(language, context=self.contents)
        if self.token_count <= 500:
            translate_all(language, context=self.contents)

    def get_all_line_texts_with_numbers(self, index=1) -> dict:
        line_texts = {}
        for content in self.contents:
            if isinstance(content, TextComponent):
                line_texts.update(content.get_all_line_texts_with_numbers(index))
            elif isinstance(content, Line):
                if content.text == "":
                    continue
                line_texts[index] = content.text
                index += 1
        return line_texts


@dataclass
class Line:
    _text: str = field(default="")
    _token_count: int | None = field(default=None, init=False)
    kind = "line"

    def __post_init__(self):
        self.text = remove_noise_space(self._text)

    @property
    def contents(self):
        return self._text

    @property
    def title(self):
        return ""

    @property
    def call_titles(self):
        return ""

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = remove_noise_space(value)
        self._token_count = None

    @property
    def token_count(self) -> int:
        if not self._token_count:
            self._token_count = count_llm_tokens(self._text)
        return self._token_count

    @property
    def show_conets(self):
        return self._text

    @property
    def show_conets_with_title(self):
        return self._text

    def __repr__(self):
        return f"{self.__class__.__name__}({self._text})"

    def __str__(self):
        return self._text

    @property
    def word_count(self) -> int:
        return len(self._text.split())

    @property
    def char_count(self) -> int:
        return len(self._text)

    @property
    def line_count(self):
        return 1

    @property
    def chapter_count(self):
        return 0

    @property
    def section_count(self):
        return 0

    @property
    def paragraph_count(self):
        return 0

    def translate(self, language="jp", context=None) -> str:
        return translate_text(self._text, language, context)


# NOTE: in some book, Paragraphs are not used.
@dataclass
class Paragraph(TextComponent):
    contents: list[Line] = field(default_factory=list)
    kind = "paragraph"

    @property
    def title(self):
        if self._title == "":
            return "NO_PARAGRAPH_TITLE"
        return self._title

    @property
    def chapter_count(self):
        return 0

    @property
    def section_count(self):
        return 0

    @property
    def paragraph_count(self):
        return 1


# NOTE: in some book, sections are not used.
@dataclass
class Section(TextComponent):
    contents: list[Paragraph | Line] = field(default_factory=list)
    kind = "section"

    @property
    def title(self):
        if self._title == "":
            return "NO_SECTION_TITLE"
        return self._title

    @property
    def chapter_count(self):
        return 0

    @property
    def section_count(self):
        return 1


@dataclass
class Chapter(TextComponent):
    contents: list[Section | Paragraph | Line] = field(default_factory=list)
    kind = "chapter"

    @property
    def title(self):
        if self._title == "":
            return "NO_CHAPTER_TITLE"
        return self._title

    @property
    def chapter_count(self):
        return 1

    @property
    def section_count(self):
        return sum(content.section_count for content in self.contents)

    @property
    def paragraph_count(self):
        return sum(content.paragraph_count for content in self.contents)


@dataclass
class Book(TextComponent):
    _title: str = field(default="NO_BOOK_TITLE")
    contents: list[Chapter | Paragraph | Line] = field(default_factory=list)
    kind = "book"
