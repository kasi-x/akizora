from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from enum import Enum

from dotenv import load_dotenv
from structlog import get_logger

from logger_config import configure_logger
from src.translate_domain import LLM
from src.translate_domain import LLM_TYPE

# from src.translate_domain import ParsedTranslateResults
# from src.translate_domain import Prompt
# from src.translate_domain import PromptContext
# from src.translate_domain import TranslateResult

configure_logger()
logger = get_logger().bind(module="data_structure")

load_dotenv("GOOGLE_API_KEY")

type TranslatedLine = str
type NATIVE_CONTENT = str


def remove_noise_space(text: str) -> str:
    return text.strip()
    # NOTE: In some case the latter can be better.
    # return re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # NOTE: I remove wastefull whitespace.
    # But in some case, like Askey Art, could use whitespace as art. But Novel's text maight not use white space as an art.


class Language(Enum):
    # ISO 639-3
    jpn = "Japanese"
    eng = "English"  # US English vs UK English
    undifined = "undifined"


type LANGUAGE_MAP_RESULT = dict[Language, dict[LLM_TYPE, TranslatedLine]]
type LANGUAGE_MAP_TOKEN = dict[Language, dict[LLM_TYPE, int]]


@dataclass
class TextComponent:
    contents: list["TextComponent"] = field(default_factory=list)
    _title: str = field(default="")
    kind = "Base text componententent"
    base_language: Language | None = None

    def __post_init__(self):
        if self.kind != "line":
            for content in self.contents:
                content.base_language = self.base_language

    def __iter__(self) -> Iterable:
        return iter(self.contents)

    @property
    def content(self) -> "TextComponent":
        return self.contents[0]

    @property
    def show_conets(self):
        return [content.show_conets for content in self.contents]

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

    def get_token_count(self, language: Language, llm_name: LLM_TYPE) -> int:
        return sum(content.get_token_count(language, llm_name) for content in self.contents)

    def set_token_count(self, language: Language, model: LLM, value: int) -> None:
        for content in self.contents:
            content.set_token_count(language, model, value)

    @property
    def show_conets_with_title(self):
        result = ""
        for content in self.contents:
            if not isinstance(content, Line) and content._title:
                result += f"-----{content.kind} : {content.title}-----\n\n"
            result += content.show_conets_with_title + "\n"

        return result

    def __str__(self):
        return self.show_conets_with_title

    @property
    def lines(self) -> list["Line"]:
        return self._get_lines(self.contents)

    def _get_lines(self, contents: list["TextComponent"]) -> list["Line"]:
        lines = []
        for item in contents:
            lines.extend(self._get_lines(item.contents))
        return lines

    @property
    def title(self):
        return self._title if self._title else "NO_TITLE"

    @property
    def char_count(self) -> int:
        return sum(content.char_count for content in self.contents)

    @property
    def word_count(self) -> int:
        return sum(content.word_count for content in self.contents)

    @property
    def line_count(self) -> int:
        return sum(content.line_count for content in self.contents)

    def add_id(self, start_count=0):
        count = start_count
        for content in self.lines:
            content.id = count
            count += 1
        return count

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


@dataclass
class Line(TextComponent):
    _text: NATIVE_CONTENT = ""
    _title: str = field(default="")
    kind = "line"
    base_language: Language | None = None
    _translated_map: LANGUAGE_MAP_RESULT = field(default=defaultdict(), init=False)
    id: int = field(default=-1, init=False)
    _token_count_map: LANGUAGE_MAP_TOKEN = field(default=defaultdict(), init=False)

    def get_token_count(self, language: Language, llm_name: LLM_TYPE) -> int | None:
        try:
            return self._token_count_map[language][llm_name]
        except KeyError:
            return None

    def set_token_count(self, language: Language, model: LLM, force=False) -> None:
        if not force and self.get_token_count(language, model.name):
            logger.info(
                "token count is already set",
                at="set_token_count_map",
                language=language,
                model=model.name,
                line=self,
            )
        self._token_count_map[language][model.name] = model.count_tokens(self.text)

    def get_selected_language_text(
        self, language: Language, llm_name: LLM_TYPE
    ) -> str | TranslatedLine | None:
        try:
            return self._translated_map[language][llm_name]
        except KeyError as e:
            logger.info(
                "failed to get selected language text",
                at="get_selected_language_text",
                error=e,
                language=language,
                llm_name=llm_name,
                line=self,
            )
            return None

    def set_selected_language_text(
        self, language: Language, llm_name: LLM_TYPE, result: TranslatedLine
    ) -> None:
        self._translated_map[language][llm_name] = result

    @property
    def text(self) -> NATIVE_CONTENT:
        return self._text

    @text.setter
    def text(self, value: NATIVE_CONTENT) -> None:
        self._text = remove_noise_space(value)

    @property
    def content(self) -> NATIVE_CONTENT:
        return self.text

    @property
    def lines(self) -> list["Line"]:
        return [self]

    @property
    def contets(self) -> list["Line"]:
        return [self]

    def _get_lines(self) -> list["Line"]:
        return [self]

    @property
    def title(self):
        return ""

    @property
    def show_conets(self):
        return self.text

    @property
    def show_conets_with_title(self):
        return self.text

    def __str__(self):
        return self.text

    def add_id(self):
        msg = "Line children cann't have id."
        raise ValueError(msg)

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    @property
    def char_count(self) -> int:
        return len(self.text)

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


# RATIONAL: Change data stracture for make higer-priority for Line.
# The data is based on Book. Howerver the most important data is Line and we treat line as first object. So the additional information of chapter, sentence, paragraph should be inside Line for simple useage. (Maybe not need to rewrite all for this purpose.)
# RAIONAL2 : I should have line and stracture separate data-stractures and adapter.


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
    base_language: str = "en"
    kind = "book"
