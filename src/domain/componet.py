from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from typing import Self
from typing import TypedDict

from dotenv import load_dotenv
from structlog import get_logger

from domain.llm import LLM
from domain.llm import LLM_TYPE_NAME
from domain.llm import LanguageEnum
from logger_config import configure_logger

configure_logger()
logger = get_logger().bind(module="book_domain")

load_dotenv("GOOGLE_API_KEY")

type TranslatedLine = str
type NATIVE_CONTENT = str
type Language = str


class InputValueError(ValueError):
    pass


type LANGUAGE_MAP_RESULT = dict[Language, dict[LLM_TYPE_NAME, TranslatedLine]]
type LANGUAGE_MAP_TOKEN = dict[Language, dict[LLM_TYPE_NAME, int]]


@dataclass
class AuthorName:
    raw_name: str


@dataclass
class AuthorInfo:
    author: AuthorName | list[AuthorName] = AuthorName(raw_name="")
    author_id: str | None = None
    author_wiki: str | None = None


@dataclass
class ContentInfo:
    book_title: str = ""
    language_code: str = ""
    nation = ""
    language: Language = field(init=False)
    publication_date: str = ""

    def __post_init__(self):
        if not self.language and self.language_code:
            self.language = LanguageEnum[self.language_code].value
        if not self.language and not self.language_code:
            raise InputValueError("Language is not set")

    def get_language(self):
        return self.language


@dataclass
class TranslateResult:
    translated_map: LANGUAGE_MAP_RESULT = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(str)), init=True
    )


class Counters(TypedDict):
    token_count: int
    char_count: int
    word_count: int
    sentence_count: int


@dataclass
class TextComponent:
    contents: list[Self] = field(default_factory=list)
    depth_level: int | None = None
    ids: dict = field(default_factory=lambda: defaultdict(int))
    counters = Counters(token_count=0, char_count=0, word_count=0, sentence_count=0)
    kind: str = ""
    part_title: str = field(default="")
    content_info: ContentInfo | None = None

    def __post_init__(self):
        self.kind = self.__class__.__name__.lower()

    def calc_stats(self, model: LLM | None = None, is_token_calc=False) -> None:
        self.counters["sentence_count"] = len(self.sentences)
        self.counters["word_count"] = self._loop(self._word_count, "word_count")
        self.counters["char_count"] = self._loop(self._char_count, "char_count")
        if is_token_calc:
            self.counters["token_count"] = self._loop(self._token_count, "token_count", model)

    def _loop(self, func, key, *args) -> int:
        if self.counters.get(key):
            return self.counters.get(key)

        if isinstance(self.a_content, TextComponent):
            value = 0
            for content in self.contents:
                value += content._loop(func, key)
        else:
            value = func(self.a_content, *args)
        self.counters[key] = value
        return value

    @staticmethod
    def _word_count(sentence: str) -> int:
        return len(sentence.split())

    @staticmethod
    def _char_count(sentence: str) -> int:
        return len(sentence)

    @staticmethod
    def _token_count(sentence: str, model: LLM | None = None) -> int:
        if model is None:
            raise ValueError("model is not set")
        return model.calc_tokens(sentence)

    def __iter__(self) -> Iterable:
        return iter(self.contents)

    def __str__(self):
        return self._show_contents()

    @property
    def a_content(self) -> Self | NATIVE_CONTENT:
        if isinstance(self.contents, list):
            return self.contents[0]  # type: ignore
        if isinstance(self.contents, str):
            return self.contents
        msg = "data structure is wrong"
        raise ValueError(msg)

    def _show_contents(self):
        result = ""
        if isinstance(self.a_content, TextComponent):
            for child_contents in self.contents:
                if self.part_title:
                    result += f"<{self.kind}>{self.part_title}_{self.ids[self.kind]}\n"
                    result += (
                        f"-----{self.kind}(f{self.ids[self.kind]}) : {self.part_title}-----\n\n"
                    )
                    result += child_contents._show_contents()
                    result += "\n"
                else:
                    result += f"-----{self.kind}(f{self.ids[self.kind]})-----\n\n"
                    result += child_contents._show_contents()
                    result += "\n"
        result += f"<{self.ids['serial_id']}>{self.a_content}"
        return result

    @property
    def sentences(self) -> list["Sentence"]:  # type: ignore
        return self._get_sentences()

    def _get_sentences(self) -> list["Sentence"]:  # type: ignore
        sentences = []
        if isinstance(self.a_content, TextComponent):
            for item in self.contents:
                sentences.extend(item._get_sentences())
        else:
            sentences.append(self.a_content)
        return sentences

    def make_count(self, kinds: str | list[str] | None = None) -> None:
        for kind in self.ids:
            if kinds != "serial_id":
                self.ids[kind] = self._count_with_kind(kind)
            if kinds == "serial_id":
                self._make_serial_id_id()

    def _make_serial_id_id(self):
        count = 0
        for sentence in self.sentences:
            sentence.ids["serial_id"] = count
            count += 1

    def _count_with_kind(self, kind: str, count: int = 0):
        contents = self.contents
        if isinstance(self.a_content, TextComponent):
            for child_contents in contents:
                if child_contents.kind == kind:
                    count += 1
                    count = child_contents._count_with_kind(kind, count)
                else:
                    count = child_contents._count_with_kind(kind, count)
            msg = "data structure is wrong"
            raise ValueError(msg)
        else:
            return count

    def __len__(self) -> int:
        return len(self.contents)
