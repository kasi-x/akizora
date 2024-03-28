from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from typing import Optional

from dotenv import load_dotenv
from structlog import get_logger

from src.llm_domain import LLM
from src.llm_domain import LLM_TYPE_NAME
from src.llm_domain import LanguageEnum
from src.logger_config import configure_logger

configure_logger()
logger = get_logger().bind(module="book_domain")

load_dotenv("GOOGLE_API_KEY")

type TranslatedLine = str
type NATIVE_CONTENT = str
type Language = str


def remove_noise_space(text: str) -> str:
    return text.replace("\n", " ").strip()
    # NOTE: In some case the latter can be better.
    # return re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # NOTE: I remove wastefull whitespace.
    # But in some case, like Askey Art, could use whitespace as art. But Novel's text maight not use white space as an art.


type LANGUAGE_MAP_RESULT = dict[Language, dict[LLM_TYPE_NAME, TranslatedLine]]
type LANGUAGE_MAP_TOKEN = dict[Language, dict[LLM_TYPE_NAME, int]]


@dataclass
class TextComponent:
    contents: list["TextComponent"]
    base_language: LanguageEnum | None = field(default=None, init=False)
    _title: str = field(default="")
    kind = "Base text componententent"

    def __iter__(self) -> Iterable:
        return iter(self.contents)

    @property
    def a_content(self) -> "TextComponent":
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

    def get_token_count(self, language: LanguageEnum, model: LLM) -> int:
        return sum(content.get_token_count(language, model) for content in self.contents)

    def set_token_count(
        self, language: LanguageEnum, model: LLM, force_update: bool = False
    ) -> None:
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

    def init_id(self):
        self.add_id()
        for content in self.contents:
            content.init_id()

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
class Components(TextComponent):
    contents: list["TextComponent"]
    kind: str = field(default="")
    _title: str = field(default="")

    def __post_init__(self):
        self.kind = f"chunk_of_{self.contents[0].kind}"
        self._title = f"chunk_of_{self.contents[0]._title}"

    def __getitem__(self, key: int) -> "TextComponent":
        return self.contents[key]


@dataclass
class Sentence(TextComponent):
    contents: list[NATIVE_CONTENT] = field(default_factory=list)


@dataclass
class Line(TextComponent):
    _text: NATIVE_CONTENT = ""
    contents: list[NATIVE_CONTENT] = field(default_factory=list)
    _title: str = field(default="")
    # kind = "line"
    id: int = field(default=-1, init=False)
    chapter_id: int | None = field(default=None, init=False)
    section_id: int | None = field(default=None, init=False)
    paragraph_id: int | None = field(default=None, init=False)
    _translated_map: LANGUAGE_MAP_RESULT = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(str)), init=True
    )
    _token_count_map: LANGUAGE_MAP_TOKEN = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(int)), init=True
    )

    def __post_init__(self):
        self._text = remove_noise_space(self._text)
        self.contents = [self.text]

    def make_sentences_from_line(self) -> list[Sentence]:
        def _split_withoute_remove_delimiter(text: str, delimiter: str) -> list[str]:
            results = text.split(delimiter)
            if len(results) != 1:
                for i in range(len(results) - 2):
                    results[i] += delimiter
            return results

        proto_sentences = [self.text]
        results = []
        for delimiter in [".", "!", "?"]:
            for proto_sentence in proto_sentences:
                results.append(_split_withoute_remove_delimiter(proto_sentence, delimiter))
                # DESIGN: I don't update iterator while iterating for avoiding unexpected behavior.
            proto_sentences = results
            results = []
        sensentences = []
        for proto_sentence in proto_sentences:
            sensentences.append(Sentence(contents=proto_sentence))
        return sensentences

    # DESIGN: this function is not close of book_domain. It is adapter between llm and book.
    # TODO: This function depends on llm_domain. So it should move outside..
    # NOTE: To make translated_line or token_counted line may be beetr but it increase complexity.
    def get_token_count(self, language: LanguageEnum, model: LLM) -> int:
        return self._token_count_map[language.value][model.name]  # type: ignore

    def set_token_count(self, language: LanguageEnum, model: LLM, force_update=False) -> None:
        if (not force_update) and self.get_token_count(language, model) > 0:
            print("pass")
            logger.info(
                "token count is already set",
                at="set_token_count_map",
                language=language.value,
                model=model.name,
                line=self.text,
            )
        self._token_count_map[language.value][model.name] = model.calc_tokens(self.content)  # type: ignore

    def get_selected_language_text(
        self, language: LanguageEnum, model: LLM
    ) -> str | TranslatedLine | None:
        try:
            return self._translated_map[language.value][model.name]  # type: ignore
        except KeyError as e:
            logger.info(
                "failed to get selected language text",
                at="get_selected_language_text",
                error=e,
                language=language.value,
                llm_name=model.name,
                line=self.text,
            )
            return None

    def set_selected_language_text(
        self, language: LanguageEnum, model: LLM, result: TranslatedLine
    ) -> None:
        self._translated_map[language.value][model.name] = result  # type: ignore

    @property
    def text(self) -> NATIVE_CONTENT:
        return self._text

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

    def init_id(self):
        pass
        # msg = "Line children cann't have id."
        # raise ValueError(msg)

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
    contents: list[Line]
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

    def add_id(self, start_count=0):
        count = start_count
        for content in self.lines:
            content.paragraph_id = count
            count += 1


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

    def add_id(self, start_count=0):
        count = start_count
        for content in self.lines:
            content.section_id = count
            count += 1


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

    def add_id(self, start_count=0):
        count = start_count
        for content in self.lines:
            content.chapter_id = count
            count += 1


@dataclass
class Book(TextComponent):
    _title: str = field(default="NO_BOOK_TITLE")
    contents: list[Chapter | Paragraph | Line] = field(default_factory=list)
    from_language: LanguageEnum = LanguageEnum.eng
    kind = "book"

    def add_id(self, start_count=0):
        count = start_count
        for content in self.lines:
            content.id = count
            count += 1

    def __post_init__(self):
        self.init_id()
