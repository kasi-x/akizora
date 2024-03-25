from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field

from dotenv import load_dotenv
from structlog import get_logger

from src.llm_domain import LLM
from src.llm_domain import LLM_TYPE
from src.llm_domain import Language
from src.logger_config import configure_logger

configure_logger()
logger = get_logger().bind(module="book_domain")

load_dotenv("GOOGLE_API_KEY")

type TranslatedLine = str
type NATIVE_CONTENT = str


def remove_noise_space(text: str) -> str:
    return text
    # return text.strip()
    # NOTE: In some case the latter can be better.
    # return re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # NOTE: I remove wastefull whitespace.
    # But in some case, like Askey Art, could use whitespace as art. But Novel's text maight not use white space as an art.


type LLM_TYPE_NAME = str
type LANGUAGE_MAP_RESULT = dict[Language, dict[LLM_TYPE_NAME, TranslatedLine]]
type LANGUAGE_MAP_TOKEN = dict[Language, dict[LLM_TYPE_NAME, int]]


@dataclass
class TextComponent:
    contents: list["TextComponent"]
    _title: str = field(default="")
    kind = "Base text componententent"
    base_language: Language | None = None

    def __post_init__(self):
        # NOTE: It can be a book what written in multiple languages. But I didn't consider it.
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
        return self._title if self._title else ""

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

    def get_token_count(self, language: Language, llm_name: LLM_TYPE_NAME) -> int:
        return sum(content.get_token_count(language, llm_name) for content in self.contents)

    def set_token_count(self, language: Language, model: LLM, force_update: bool = False) -> None:
        for content in self.contents:
            content.set_token_count(language, model, force_update)

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
        return self._get_lines()

    def _get_lines(self) -> list["Line"]:
        lines = []
        for item in self.contents:
            lines.extend(item._get_lines())
        return lines

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
    contents: list[NATIVE_CONTENT] = field(default_factory=list)
    _title: str = field(default="")
    kind = "line"
    base_language: Language | None = None
    id: int = field(default=-1, init=False)
    _translated_map: LANGUAGE_MAP_RESULT = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(str)), init=True
    )
    _token_count_map: LANGUAGE_MAP_TOKEN = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(int)), init=True
    )

    # DESIGN: this function is not close of book_domain. It is adapter between llm and book.
    # TODO: This function depends on llm_domain. So it should move outside..
    # NOTE: To make translated_line or token_counted line may be beetr but it increase complexity.
    def get_token_count(self, language: Language, llm_name: LLM_TYPE_NAME) -> int:
        return self._token_count_map[language][llm_name]

    def set_token_count(self, language: Language, model: LLM, force_update=False) -> None:
        if (not force_update) and self.get_token_count(language, model.name) > 0:
            print("pass")
            logger.info(
                "token count is already set",
                at="set_token_count_map",
                language=language,
                model=model.name,
                line=self.text,
            )
        self._token_count_map[language][model.name] = model.calc_tokens(self.content)

    def get_selected_language_text(
        self, language: Language, llm_name: LLM_TYPE_NAME
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
                line=self.text,
            )
            return None

    def set_selected_language_text(
        self, language: Language, llm_name: LLM_TYPE_NAME, result: TranslatedLine
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

    def _get_lines(self) -> list["Line"]:
        return [self]

    @property
    def contets(self) -> list["Line"]:
        return [self]

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


type Lines = list[Line]

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
    base_language: Language
    kind = "book"

    def __post_init__(self):
        self.add_id()
