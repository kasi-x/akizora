from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from typing import Union

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv("GOOGLE_API_KEY")

model = genai.GenerativeModel("gemini-pro")
# genai.configure(api_key=GOOGLE_API_KEY)


def count_llm_tokens(text: str) -> int:
    if text in ("", " ", "\n", "\t", "\r"):
        return 0
    return model.count_tokens(text).total_tokens


def remove_noise_space(text: str) -> str:
    return text.strip()
    # NOTE: In some case the latter can be better.
    # return re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # NOTE: I remove wastefull whitespace.
    # But in some case, like Askey Art, could use whitespace as art. But Novel's text maight not use white space as an art.


# RATIONAL: Change data stracture for make higer-priority for Line.
# The data is based on Book. Howerver the most important data is Line and we treat line as first object. So the additional information of chapter, sentence, paragraph should be inside Line for simple useage. (Maybe not need to rewrite all for this purpose.)
# RAIONAL2 : I should have line and stracture separate data-stractures.


@dataclass
class Translator:
    input_token_border: int
    output_token_limit: int
    en_to_jp: float
    jp_to_en: float

    def translate_text(self, text: str, language="jp", context=None) -> str:
        text = self.build_text(text, language, context)
        return self.call_llm(text)

    def call_llm(self, text: str) -> str:
        return "not implemented"

    def build_text(self, text: str, language: str, context=None) -> str:
        if context:
            text = self.append_context(language, text, context)
        return text

    def append_context(self, language, target_content, wide_contents) -> str:
        text = f"""
        I give you novel's context.
        === {wide_contents} ===
        In the following sentence, please translate only the next content inside '<>' into {language}.
        <{target_content}>"""
        return text

    def is_able_translate_all_words(
        self,
        input_token_count: int,
        output_token_count=None,
        input_language="en",
        target_language="jp",
    ) -> bool:
        if input_token_count > self.input_token_border:
            return False
        if output_token_count and output_token_count > self.output_token_limit:
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


class GEMINI_PRO(Translator):
    def __init__(self):
        super().__init__(
            input_token_border=30720, output_token_limit=2048, en_to_jp=4, jp_to_en=0.25
        )
        self.model = genai.GenerativeModel("gemini-pro")

    def call_llm(self, text: str) -> str:
        result = ""
        response = model.generate_content(text)
        for chunk in response:
            result += chunk.text
        return result


@dataclass
class GPT(Translator):
    def __init__(self):
        pass  # TODO: Implement GPT's Translator


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

    def translate(self, language="jp", model=GEMINI_PRO, context=None) -> None:
        if self.token_count > 10000 or context:
            for content in self.contents:
                content.translate(language, model, context)
        if 500 < self.token_count <= 20000:
            for content in self.contents:
                content.translate(language, model, context=self.contents)
        if self.token_count <= 500:
            self.translate_all(language, model)

    def update_translated_text(self, base_text, translated_text) -> None:
        for content in self.contents:
            if isinstance(content, Line) and content.contents == base_text:
                content.translated = translated_text
                break

            self.update_translated_text(base_text, translated_text)

    # REFACTOR: This method is too long. It should be refactored.
    def translate_all(self, language="jp", model=GEMINI_PRO) -> None:
        lines_with_index = self.get_all_line_texts_with_numbers()
        # MEMO: Maybe we don't need to sort the dictionary.(I didn't check it yet.)
        lines_with_index = dict(sorted(lines_with_index.items()))
        base_text = ""
        # TODO: CHECK how we can improve the following prompt.
        # REFACTOR: this prompt and method should move to Translator class.
        prompt = f"""Translate text into {language} with index number like "<1>hello <2>world." into "<1>こんにちは <2>世界." The following sentences is the original text.\n"""
        base_text += prompt
        for index, line in lines_with_index.items():
            base_text += f"<{index}> {line}"

        translated_text = model.call_llm(base_text)
        translated_dict = {}
        for index in lines_with_index:
            tag_start = translated_text.find(f"<{index}>")
            if tag_start == -1:
                continue
            tag_end = tag_start + len(f"<{index}>")

            next_tag_start = translated_text.find(f"<{index + 1}>")
            if next_tag_start == -1:
                next_tag_start = len(translated_text) - 1
                break

            translated_dict[index] = translated_text[tag_end + 1 : next_tag_start - 1]
        # MEMO: making translated_dict is finished in this line.

        # MEMO: Start matching the translated text with the original text for save translated_text in accurate place.
        for translated_dict_index, translated_text in translated_dict.values():
            base_text = lines_with_index.get(translated_dict_index, "")
            if not base_text:
                print(f"Index <{index}> is not found in lines_with_index dictionary.")
                continue
            self.update_translated_text(base_text, translated_text)

    def get_content(
        self, kind: str = "line", contents=None
    ) -> list[Union["TextComponent", "Line"]]:
        result = []
        if not contents:
            contents = self.contents
        for content in contents:
            # if isinstance(content, Line):  # it's almost ok, but if you want to grep chapter/section/paragraph, you should use 'kind' argument.
            if content.kind == kind:
                result.append(content)
            else:
                # TYPE: Line don't have 'get_contents' method but it's okay.
                result.extend(self.get_contents(kind, content.contents))  # type: ignore
        return result

    def get_all_line_texts_with_numbers(self, index=0) -> dict:
        line_text_dict = {}
        lines: list[Lines] = self.get_contents(kind="line")  # type: ignore
        for line in lines:
            if line.contents == "":
                continue
            line_text_dict[index] = line.contents
            index += 1
        return line_text_dict


@dataclass
class Line:
    _text: str = field(default="")
    _token_count: int | None = field(default=None, init=False)
    kind = "line"
    translated: str = field(default="")

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

    def translate(self, language="jp", model=GEMINI_PRO, context=None) -> str:
        return model.translate_text(self.contents, language, context)  # type: ignore


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


# NOTE: in some book, Sections are not used.
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
