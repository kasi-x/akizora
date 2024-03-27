import re
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from typing import Optional

from dotenv import load_dotenv
from structlog import get_logger

from src.book_domain import Book
from src.book_domain import Components
from src.book_domain import LanguageEnum
from src.book_domain import Line
from src.book_domain import Lines
from src.book_domain import TextComponent
from src.book_domain import TranslatedLine
from src.llm_domain import LLM
from src.logger_config import configure_logger

configure_logger()
logger = get_logger().bind(module="translate_domain")

load_dotenv("GOOGLE_API_KEY")

type PromptScript = str
type RAW_LLM_RESOPNSE = str


class TargetLineEmptyError(Exception):
    pass


class PromptSizeError(Exception):
    pass


class ContextParseError(Exception):
    pass


type SomeTextComponent = TextComponent | list[TextComponent]


def is_not_noise(line: Line) -> bool:
    return line.text.strip() != ""


def remove_empty_lines(lines: Lines) -> Lines:
    return [line for line in lines if is_not_noise(line)]


@dataclass
class PromptContext:
    lines: Lines
    from_language: LanguageEnum
    to_language: LanguageEnum
    contextual_lines: Lines | None = field(default=None)

    def to_language_str(self) -> str:
        return self.to_language.value

    def from_language_str(self) -> str:
        return self.from_language.value

    def get_input_token_count(self, model: LLM) -> int:
        if self.contextual_lines:
            sum(
                [line.get_token_count(self.from_language, model) for line in self.contextual_lines]
            )
        return sum([line.get_token_count(self.from_language, model) for line in self.lines])

    def get_output_token_count(self, model: LLM) -> int:
        input_translate_token = sum(
            [line.get_token_count(self.from_language, model) for line in self.lines]
        )
        braket_token = 0
        if len(self.lines) > 2:
            # NOTE: bracket token maybe 2 token(Not accurate). braeket is `<1> line one <2> line two`'s `<1>, <2>`
            braket_token = 2 * len(self.lines)
        translate_rate = model.calc_token_rate(self.from_language, self.to_language)
        return input_translate_token * translate_rate + braket_token


@dataclass
class ParsedTranslateResults:
    translated_lines: dict[int, TranslatedLine]
    base_lines: Lines
    context: PromptContext


@dataclass
class TranslateResult:
    text: RAW_LLM_RESOPNSE
    context: PromptContext

    def is_parsible(self) -> bool:
        if len(self.context.lines) > 1 or self.context.contextual_lines:
            return True
        return False

    def try_parsing_translated_result(self) -> ParsedTranslateResults:
        # EXAMPLE: when text is <1>hello <2>world <3>good morning, the result is {'1': 'hello', '2': 'world', '3': 'good morning'}
        pattern = r"<(\d+)>(.*?)((?=<\d+>)|$)"
        try:
            matches = re.findall(pattern, self.text)
            parsed_result = {}
            for match in matches:
                parsed_result[int(match[0])] = match[1].strip()
            base_lines = self.context.lines
            if len(self.context.lines) == len(parsed_result):
                return ParsedTranslateResults(
                    translated_lines=parsed_result, base_lines=base_lines, context=self.context
                )
            else:
                logger.error(
                    "failed to parse multi translated text",
                    at="parse_multi_translated_text",
                    error="The number of translated text and the number of target text is not same.",
                    target_lines=self.context.lines,
                    context_lines=self.context.contextual_lines,
                    text=self.text,
                    prompt=self.context,
                    match=match,
                    matches=matches,
                )
                msg = "The number of translated text and the number of target text is not same."
                raise ContextParseError(msg)
        except Exception as e:
            logger.exception(
                "failed to parse multi translated text",
                at="parse_multi_translated_text",
                error=e,
                text=self.text,
                prompt=self.context,
                matches=matches,
            )
            msg = f"failed to parse multi translated text {e}"
            raise ValueError(msg)


def component_to_lines(component: SomeTextComponent) -> Lines:
    if isinstance(component, list):
        result = []
        for a_component in component:
            result.extend(a_component.lines)
            return result
    return component.lines


@dataclass
class Prompt:
    script: str
    context: PromptContext


class PromptBuilder(ABC):
    template = ""
    template_token = None

    @abstractmethod
    def build(self, context: PromptContext) -> Prompt:
        pass

    def get_template_token(self, model: LLM) -> int:
        if not self.template_token:
            self.template_token = model.calc_tokens(self.template)
        return self.template_token


class SingleLineTranslatePromptBuilder(PromptBuilder):
    template = "Translate following sencente into `Language`\n"

    def build(self, context: PromptContext) -> Prompt:
        prompt_template = f"Translate following sencente into {context.to_language_str()}\n {context.lines[0].text}"
        return Prompt(script=prompt_template, context=context)


class MultiLineTranslatePromptBuilder(PromptBuilder):
    template = (
        """Please translate the following sentences into  `Language` with <number> tag text.\n"""
    )

    def build(self, context: PromptContext) -> Prompt:
        prompt_template = f"""Please translate the following sentences into {context.to_language_str()} with <number> tag text.\n"""
        result = prompt_template
        for local_index, text in enumerate(context.lines):
            result += f"<{local_index}>{text} "
        return Prompt(result.strip(), context)


class ContextualTranslatePromptBuilder(PromptBuilder):
    template = """Please translate the only following sentences between <start> and <end> into `Language` with <number> tag text.\n"""

    def build(self, context: PromptContext) -> Prompt:
        prompt_template = f"""Please translate the only following sentences between <start> and <end> into {context.to_language_str()} with <number> tag text."""
        result = prompt_template
        is_inside_target_index = False
        local_index = 0
        for line in context.contextual_lines:  # type: ignore
            if line in context.lines:
                if not is_inside_target_index:
                    is_inside_target_index = True
                    result += f"\n<start><{local_index}>{line.text}"
                else:
                    result += f"\n<{local_index}>{line.text}"
                local_index += 1
            elif is_inside_target_index:
                result += f"\n<end>{line.text}"
                is_inside_target_index = False
            else:
                result += f"\n{line.text}"
        if is_inside_target_index:
            result += "<end>"
        return Prompt(result.strip().lstrip("\n"), context)


class PromptManager:
    def __init__(self, model: LLM) -> None:
        self.model = model

    def calculate_input_token(self, context: PromptContext) -> int:
        return context.get_input_token_count(self.model) + self.select_builder(
            context
        ).get_template_token(self.model)

    def calculate_output_token(self, context: PromptContext) -> int:
        return context.get_output_token_count(self.model)

    def is_able_to_translate(self, context: PromptContext) -> bool:
        return self.is_able_to_send_prompt(context) and self.is_able_to_get_output(context)

    def is_able_to_send_prompt(self, context: PromptContext) -> bool:
        return self.model.is_input_token_affording(self.calculate_input_token(context))

    def is_able_to_get_output(self, context: PromptContext) -> bool:
        return self.model.is_output_token_affording(
            context.get_output_token_count(self.model), context.from_language, context.to_language
        )

    def build_prompt(self, context: PromptContext) -> Prompt:
        return self.select_builder(context).build(context)

    def select_builder(self, context: PromptContext) -> PromptBuilder:
        if len(context.lines) == 1:
            return SingleLineTranslatePromptBuilder()
        elif context.contextual_lines:
            return ContextualTranslatePromptBuilder()
        else:
            return MultiLineTranslatePromptBuilder()


class Translater:
    def __init__(self, model: LLM) -> None:
        self.model = model

    def build_translate_prompt(self, context: PromptContext) -> Prompt:
        return PromptManager(self.model).build_prompt(context)

    def translate(self, text) -> str:
        return self.model.call_llm(text)

    def translate_prompt(self, context: PromptContext) -> TranslateResult:
        prompt = self.build_translate_prompt(context)
        return TranslateResult(text=self.translate(prompt.script), context=context)

    def parse_translate_result(self, translate_result) -> ParsedTranslateResults:
        return translate_result.try_parsing_translated_result()


class BookTranslaor:
    def __init__(self, model: LLM, to_language: LanguageEnum, from_language: LanguageEnum) -> None:
        # self.book = book
        self.model = model
        self.to_language = to_language
        # if not from_language:
        # self.from_language = book.base_language
        # else:
        self.from_language = from_language
        # self.calc_book_token_count()
        self.translater = Translater(model)
        self.prompt_manager = PromptManager(model)

    def calc_component_token_count(self, component: TextComponent, force_update=False) -> None:
        component.set_token_count(self.from_language, self.model, force_update)

    def create_context(
        self, component: TextComponent | Components, contextual_lines=None
    ) -> PromptContext:
        return PromptContext(
            component.lines, self.from_language, self.to_language, contextual_lines
        )

    def reduce_output_from_components(self, components: Components) -> list[PromptContext]:
        print(f"components is {len(components)}")
        print(f"line is {components.lines}")
        if len(components) == 1:
            return self.create_segment_prompt_context_from_any(components[0])
        index = 1
        while len(components[:-index]) >= 1:
            current_context = self.create_context(Components(components[:-index]), None)
            if self.prompt_manager.is_able_to_translate(current_context):
                return [
                    self.create_segment_prompt_context_from_any(Components(components[:-index])),
                    self.create_segment_prompt_context_from_any(Components(components[-index:])),
                ]
            else:
                index += 1
        return [
            self.create_segment_prompt_context_from_any(components[0]),
            self.create_segment_prompt_context_from_any(Components(components[1:])),
        ]

    def reduce_output_from_a_componnent(self, a_component: TextComponent) -> list[PromptContext]:
        if isinstance(a_component, Line | str):
            logger.error(
                "failed to create prompt",
                at="create_segment_prompt_from_any",
                error="The line is too big to translate.",
                line=a_component.text,
            )
            msg = f"The line is too big to translate.{a_component}"
            raise PromptSizeError(msg)
        else:
            print(f"contents is {a_component}")
            return self.reduce_output(Components(a_component.contents))

    def reduce_output(self, component: SomeTextComponent) -> list[PromptContext]:
        if isinstance(component, Components):
            return self.reduce_output_from_components(component)
        if isinstance(component, TextComponent):
            return self.reduce_output_from_a_componnent(component)
        return None

    def create_segment_prompt_context_from_any(
        self, component: TextComponent | Components
    ) -> list[PromptContext]:
        try:
            current_context = self.create_context(component)
            if not self.prompt_manager.is_able_to_get_output(current_context):
                print("not able to get output")
                return self.reduce_output(component)
            print("able to get output")

            if not self.prompt_manager.is_able_to_send_prompt(current_context):
                print("not able to send prompt")
                return self.reduce_output(component)
            print("able to send prompt")
            # context_lines = self.append_some_context_as_long_as_affordable(component)
            # # print("context_lines", context_lines)
            # result.append(self.create_context(component, context_lines))
            # print("result", result)
            return [current_context]

        except Exception as e:
            logger.exception(
                "failed to create prompt",
                at="create_segment_prompt_from_any",
                error=e,
                component=component,
            )
            msg = f"failed to create prompt {e}"
            raise ValueError(msg)

    # def find_context_start_index(
    #     self,
    #     component: SomeTextComponent,
    #     target_line_start_index: int,
    #     target_line_end_index: int,
    # ) -> int:  # type: ignore
    #     # TODO: Not clever code here.
    #
    #     move_count = 1
    #     book_lines = self.book.lines
    #     while True:
    #         start_index_trial = target_line_start_index - move_count
    #         if start_index_trial < 0:
    #             return 0
    #         current_context = self.create_context(
    #             component, book_lines[start_index_trial : target_line_end_index + 1]
    #         )
    #         if self.prompt_manager.is_able_to_send_prompt(current_context):
    #             move_count += 1
    #         else:
    #             return start_index_trial + 1
    #
    # def find_context_end_index(
    #     self,
    #     component: SomeTextComponent,
    #     target_line_start_index: int,
    #     target_line_end_index: int,
    # ) -> int:  # type: ignore
    #     move_count = 1
    #     book_lines = self.book.lines
    #     while True:
    #         end_index_trial = target_line_end_index + move_count
    #         if end_index_trial > len(book_lines) - 1:
    #             return len(book_lines) - 1
    #         # TODO: Not clever code here.
    #         current_context = self.create_context(
    #             component, book_lines[target_line_start_index : end_index_trial + 1]
    #         )
    #         if self.prompt_manager.is_able_to_send_prompt(current_context):
    #             move_count += 1
    #         else:
    #             return end_index_trial - 1
    #
    # def append_some_context_as_long_as_affordable(
    #     self, component: SomeTextComponent
    # ) -> Lines | None:
    #     if isinstance(component, list):
    #         target_line_start_index = component[0].lines[0].id
    #         target_line_end_index = component[-1].lines[-1].id
    #     else:
    #         target_line_start_index = component.lines[0].id
    #         target_line_end_index = component.lines[-1].id
    #
    #     book_lines = self.book.lines
    #     start_index = self.find_context_start_index(
    #         component, target_line_start_index, target_line_end_index
    #     )
    #     end_index = self.find_context_end_index(component, start_index, target_line_end_index)
    #     if start_index == target_line_start_index and end_index == target_line_end_index:
    #         return []
    #     else:
    #         return book_lines[start_index:end_index]
