import re
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from typing import Union, Any
import inspect

import google.generativeai as genai
from dotenv import load_dotenv
from logger_config import configure_logger
from structlog import get_logger
from typing import TypeAlias
from enum import Enum
from abc import ABC, abstractmethod
from src.book_domain import Line, TextComponent, Language, TranslatedLine, Book

configure_logger()
logger = get_logger().bind(module="data_structure")


load_dotenv("GOOGLE_API_KEY")

PromptScript: TypeAlias  = str
RAW_LLM_RESOPNSE: TypeAlias  = str


class TargetLineEmptyError(Exception):
    pass

class PromptSizeError(Exception):
    pass

class ContextParseError(Exception):
    pass

class LLM_TYPE(Enum):
    GEMINI_PRO = "gemini-pro"
    GPT3 = "gpt3"

TOKEN_COSTS_TABLE: TypeAlias = dict[Language, int]


GEMINI_TOKEN_COST_TABLE:TOKEN_COSTS_TABLE = {
    # the amount is all of translate costs by english.
    Language.jpn: 5,
    Language.eng: 1,
}

def calc_token_rate(from_language:Language, to_language:Language, token_cost_table:TOKEN_COSTS_TABLE) -> int:
    return token_cost_table[to_language] // token_cost_table[from_language]

class LLM(ABC):
    def __init__(self, name, input_token_limit, output_token_limit, token_cost_table):
        self.name: LLM_TYPE = name
        self.input_token_limit: int = input_token_limit
        self.output_token_limit: int = output_token_limit
        self.token_cost_table: TOKEN_COSTS_TABLE = token_cost_table

    @abstractmethod
    def call_llm(self, text: str, language="jp", context=None) -> str:
        return "not implemented"

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        print("Not implemented yet")
        return -1


class GEMINI_PRO(LLM):
    def __init__(self):
        super().__init__(
            name = LLM_TYPE.GEMINI_PRO, input_token_limit=30720, output_token_limit=2048, token_cost_table=GEMINI_TOKEN_COST_TABLE,
        )
        self.model = genai.GenerativeModel("gemini-pro")

    def call_llm(self, text: str) -> str:
        result = ""
        response = self.model.generate_content(text)
        for chunk in response:
            result += chunk.text
        return result

    def count_tokens(self, text: str) -> int:
        if text in ("", " ", "\n", "\t", "\r"):
            return 0
        return self.model.count_tokens(text).total_tokens


class GPT(LLM):
    def __init__(self):
        pass  # TODO: Implement GPT's Translator

    def call_llm(self, text: str) -> str:
        return f"{text} inputed, but not implemented"

    def count_tokens(self, text: str) -> int:
        # TODO: Implement GPT's count_llm_tokens
        return 0



AnyContet :TypeAlias = TextComponent|list[TextComponent]
Lines: TypeAlias = list[Line]

def is_empty_line(line: Line) -> bool:
    return line.text.strip() == "" or line.text.strip() == "\n"

def remove_empty_lines(lines: Lines) -> Lines:
    return [line for line in lines if not is_empty_line(line)]



@dataclass
class PromptContext:
    input_data :AnyContet
    from_language: Language
    to_language: Language
    target_lines: Optional[Lines] = field(default=None)
    line : Optional[Line] = field(default=None)
    lines : Optional[Lines] = field(default=None)

    def __post_init__(self):
        self.try_parsing_input_data_into_line_or_lines()

    def try_parsing_input_data_into_line_or_lines(self) -> None:
        if isinstance(self.input_data, Line):
            self.line = self.input_data
        elif isinstance(self.input_data, list) and isinstance(self.input_data[0], Line) and len(self.input_data) == 1:
            self.line = self.input_data[0] # type: ignore
        elif isinstance(self.input_data, list):
            if isinstance(self.input_data[0], Line):
                self.lines = self.input_data # type: ignore
            else:
                self.lines = [line for component in self.input_data for line in component.lines]
        elif isinstance(self.input_data, TextComponent):
            self.lines = self.input_data.lines
        else:
            logger.error("line value isn't set.", kind="ValueTypeError", at="PromptContext", when="get_line_value", value_type= type(self.input_data), value=self.input_data)
        if self.lines:
            self.lines = remove_empty_lines(self.lines) # type: ignore
            if not self.lines:
                raise TargetLineEmptyError("The target lines are empty.")

        elif self.line and is_empty_line(self.line): # type: ignore
            self.line = None
            raise TargetLineEmptyError("The target line is empty.")
        elif not self.line and not self.lines:
            raise TargetLineEmptyError("The context is not set correctly.")


@dataclass
class Prompt:
    script: str
    context: PromptContext
    input_token : Optional[int] = field(default=None)
    expected_output_token: Optional[int] = field(default=None)

    def calc_output_token(self, model:LLM) -> None:
        token_rate = calc_token_rate(self.context.from_language, self.context.to_language, model.token_cost_table)

        if self.context.target_lines:
            self.expected_output_token = sum([line.get_token_count(self.context.from_language, model.name) for line in self.context.target_lines]) * token_rate  # type: ignore
        else:
            self.expected_output_token = sum([line.get_token_count(self.context.from_language, model.name) for line in self.context.lines]) * token_rate  # type: ignore

@dataclass
class ParsedTranslateResults:
    translated_lines: dict[int, TranslatedLine]
    base_lines: list[Line]
    context: PromptContext

@dataclass
class TranslateResult:
    text: RAW_LLM_RESOPNSE
    context: PromptContext

    def is_parsible(self) -> bool:
        if self.context.target_lines and len(self.context.target_lines) > 1:
            return True
        if self.context.lines and len(self.context.lines) > 1:
            return True
        return False


def try_parsing_translated_result(result:TranslateResult) -> ParsedTranslateResults:
    # EXAMPLE: when text is <1>hello <2>world <3>good morning, the result is {'1': 'hello', '2': 'world', '3': 'good morning'}
    pattern = r"<(\d+)>(.*?)((?=<\d+>)|$)"
    try :
        matches = re.findall(pattern, result.text)
        parsed_result = {}
        for match in matches:
            key = int(match[0])
            value = TranslatedLine(match[1].strip())
            parsed_result[key]= value
        if isinstance(result.context.target_lines, list):
            base_lines = result.context.target_lines
            if len(result.context.target_lines) == len(parsed_result):
                return ParsedTranslateResults(translated_lines=parsed_result, base_lines=base_lines, context=result.context)
            else:
                logger.error("failed to parse multi translated text", at="parse_multi_translated_text", error="The number of translated text and the number of target text is not same.", base_script=self.context.lines[self.context.target_index_range],text=self.text, prompt=self.context, matches=matches, result=result) # type: ignore
                raise ContextParseError("The number of translated text and the number of target text is not same.")
        return ParsedTranslateResults(translated_lines=result, base_lines=self.context.lines, context=result.context) # type: ignore
    except Exception as e:
        logger.error("failed to parse multi translated text", at="parse_multi_translated_text", error=e, text=self.text, prompt=self.context, matches=matches, match=match, value=value)
        raise ValueError(f"failed to parse multi translated text {e}")

# def update_line_with_translated_result(result:TranslateResult) -> None:
#     if result.is_parsible():
#         parsed_result = parse_translated_result(result)
#         for _, line in enumerate(parsed_result.base_lines):
#             line.set_selected_language_text(result.context.to_language, model.name



def make_single_line_transtlate_prompt(context: PromptContext) -> Prompt:
    prompt_template = f"Translate following sencente into {self.context.to_language}\n {self.context.line.text}"
    return Prompt(
        script=prompt_template,
        context=context,
    )

         #
 def make_multi_line_translate_prompt(context: PromptContext) -> Prompt:
     prompt_template = f"""Please translate the following sentences into {context.to_language} with <number> tag text.\n"""
     result = prompt_template

     for local_index, text in enumerate(context.lines): # type: ignore
         result += f"<{local_index}>{text} "
     return Prompt(result.strip(), context)

 def make_contextual_translate_prompt(context: PromptContext) -> Prompt:
     prompt_template = f"""Please translate the only following sentences between <start> and <end> into {context.to_language} with <number> tag text.\n"""
     result = prompt_template
     is_inside_target_index = False
     local_index = 0

     for line in context.lines: # type: ignore
         if line in context.target_lines: # type: ignore
             if not is_inside_target_index:
                 is_inside_target_index = True
                 result += f"<start><{local_index}>{line.text} "
             else:
                 result += f"<{local_index}>{line.text} "
             local_index += 1
         else:
             if is_inside_target_index:
                 result += f"<end>{line.text} "
                 is_inside_target_index = False
             else:
                 result += f"{line.text} "
     if is_inside_target_index:
         result += "<end>"
     return Prompt(result.strip(), context)


def create_translate_prompt(context:PromptContext) -> Prompt:
    if context.target_lines:
        return make_contextual_translate_prompt(context)
    elif context:
        return make_single_line_transtlate_prompt(context)
    elif context.is_multi_line():
        return make_multi_line_translate_prompt(context)
    else:
        logger.error("line value error", at="create_translate_prompt", situation="setting_up_raw_lines", line_type= type(context.line), line=context.line)
        raise ValueError("The context is not set correctly.")








class BookTranslaor:
    def __init__(self, book, model, from_language:Language=Language.eng, to_language:Language=Language.jpn):
        self.book = book
        self.model = model
        self.from_language = from_language
        self.to_language = to_language
        self.calc_book_token_count()

    def call_prompt_builder(self, context:PromptContext) -> Optional[PromptBuilder]:
        return PromptBuilder(self.model, context).create_translate_prompt()

    def create_context(self, any_content: AnyContet, target_index: Optional[int] = None) -> PromptContext:
        # when making PromptContext failed, raised TargetLineEmptyError.
        return PromptContext(input_data=any_content, from_language=self.from_language, to_language=self.to_language, target_index=target_index, tokens=self.get_token_count(any_content))

    def create_segment_prompt_from_any(self, any_content: AnyContet=None) -> list[Prompt]:
        if any_content is None:
            return self.create_segment_prompt_from_any(self.book)
        elif isinstance(any_content, TextComponent):
            return self.create_segment_prompt_from_component(any_content)
        elif isinstance(any_content, Line):
            return self.create_segment_prompt_from_line(any_content)
        elif isinstance(any_content, list) and isinstance(any_content[0], TextComponent):
            return self.create_segment_prompt_from_components(any_content)
        elif isinstance(any_content, list) and isinstance(any_content[0], Line):
            return self.create_segment_prompt_from_lines(any_content)


    def create_segment_prompt_from_lines(self, data: list[Line]) -> list[Prompt]:
        if self.is_abdle_to_send_this_content(data):
            try:
                context = self.create_context(data)
                a_prompt = self.call_prompt_builder(context).create_translate_prompt()
                return [a_prompt]
            except TargetLineEmptyError as e:
                logger.info("failed to create prompt", function_name=inspect.currentframe().f_code.co_name, error=e, data=data, context=context)
                return []
            except PromptSizeError as e:
                return self.create_segment_prompt_from_any(data[:])
            except Exception as e:
                logger.error("failed to create prompt", function_name=inspect.currentframe().f_code.co_name, error=e, data=data, context=context) # type: ignore
                raise ValueError(f"failed to create prompt {e}")
        else:
            self.create_segment_prompt_from_any(data[:])

    def create_segment_prompt_from_component(self, data: TextComponent) -> list[Prompt]:
        if self.is_abdle_to_send_this_content(data):
            try:
                context = self.create_context(data)
                a_prompt = self.call_prompt_builder(context).create_translate_prompt()
                return [a_prompt]
            except TargetLineEmptyError as e:
                logger.info("failed to create prompt", function_name=inspect.currentframe().f_code.co_name, error=e, data=data, context=context)
                return []
            except PromptSizeError as e:
                return self.create_segment_prompt_from_any(data[:])
            except Exception as e:
                logger.error("failed to create prompt", function_name=inspect.currentframe().f_code.co_name, error=e, data=data, context=context) # type: ignore
                raise ValueError(f"failed to create prompt {e}")

    # def is_able_to_create_multi_prompt_with_index(self, data: list[TextComponent], index:int) -> list[Prompt]:
    #     data, rest = data[:index], data[index:]
    #     if self.is_abdle_to_send_this_content(data):
    #         try:
    #             context = self.create_context(data)
    #             a_prompt = self.call_prompt_builder(context).create_translate_prompt()
    #             # if a_prompt.expected_output_token < 0:
    #             #     return self.is_able_to_create_multi_prompt_with_index(data, index-1)
    #
    #         except TargetLineEmptyError as e:
    #             logger.info("failed to create prompt", function_name=inspect.currentframe().f_code.co_name, error=e, data=data, context=context)
    #             return []
    #         except PromptSizeError as e:
    #             return self.create_segment_prompt_from_any(data[:])
    #         except Exception as e:
    #             logger.error("failed to create prompt", function_name=inspect.currentframe().f_code.co_name, error=e, data=data, context=context) # type: ignore
    #             raise ValueError(f"failed to create prompt {e}")



    def create_segment_prompt_from_line(self, data: Line) -> list[Prompt]: # type: ignore
         if self.is_abdle_to_send_this_content(data):
            try:
                context = self.create_context(data)
                a_prompt = self.call_prompt_builder(data).create_translate_prompt(context)
                return [a_prompt]
            except PromptSizeError as e:
                logger.error("failed to create prompt", at="create_segment_prompt_from_line", error=e, data=data)
                raise ValueError(f"failed to create prompt {e}, data={data}")
            except Exception as e:
                logger.error("failed to create prompt", function_name=inspect.currentframe().f_code.co_name, error=e, component=component, context=context) # type: ignore
                raise ValueError(f"failed to create prompt {e}")


    def create_segment_prompt_from_components(self, components: list[TextComponent]) -> list[Prompt]:
        pass


    def this_line_is_too_big_to_translate(self, line: Line) -> None:
        logger.error("one line is too big to translate", at="this_line_is_too_big_to_translate", line=line)




    # def make_prompt(self, any_content: Optional[AnyContet]=None):
    #     if any_content is None:
    #         return self.make_prompt(self.book)
    #
    #     if isinstance(any_content, Line):
    #         a_line :Line = any_content
    #         if self.is_abdle_to_send_this_content(any_content):
    #
    #
    #     if self.is_abdle_to_send_this_content(any_content):
    #         lines = any_content.lines()
    #         return [Prompt(self.build_text(any_content, self.target_language))]
    #

    # def calc_book_token_count(self) -> None:
    #     for line in self.book.lines:
    #         line.token_count[model.name][self.from_language]] = self.model.count_tokens(line.contents)


    def calc_script_token_affordability(self, prompt: Prompt) -> int:
        return self.model.input_token_limit - self.model.count_tokens(prompt.script)

    def is_abdle_to_send_this_content(self, any_content: AnyContet) -> bool:
        return self.get_token_count(any_content) <= self.model.input_token_limit

    def get_token_count(self, any_content: AnyContet) -> int: # type: ignore
        # NOTE: if token_count is None, fail to get token count. But clalc_book_token_count should be called before this method.
        if isinstance(any_content, list):
            if isinstance(any_content[0], list):
                lines :list[Line] = any_content # type: ignore
                return sum([line.token_count for line in lines])
            if isinstance(any_content[0], TextComponent):
                components :list[TextComponent] = any_content # type: ignore
                return sum([component.token_count for component in components])

        if isinstance(any_content, Line):
            line: Line = any_content
            return line.token_count

        if isinstance(any_content, TextComponent):
            component: TextComponent = any_content
            return component.token_count







    # def check_output_token_affordability(self, prompt: Prompt) -> bool:
        # return self.model.count_tokens(prompt.script) <= self.model.input_token_limit

    # def calc_prompt_output_size_afford_in_base(self, prompt_or_token: Prompt | int) -> int:
    #     if self.input_language == "en" and self.target_language == "jp":
    #         rate = self.en_to_jp
    #     elif self.input_language == "jp" and self.target_language == "en":
    #         rate = self.jp_to_en
    #     else:
    #         raise ValueError("The language is not supported.")
    #     if isinstance(prompt_or_token, Prompt):
    #         return self.output_token_limit // rate - self.model.count_tokens(prompt_or_token.raw_lines)
    #     return self.model.input_token_limit // rate - prompt_or_token
    #
    #
    #



def append_multi_context(self, language, target_content, wide_contents) -> str:
    text = f"""
    this is the context.
    === {wide_contents} ===
    Please translate only the next sentences into {language} like '<1>hello <2>world.' into '<1>こんにちは<2>世界。'
    <{target_content}>"""
    return text


def append_single_context(self, language, target_content, wide_contents) -> str:
    text = f"""
    this is the context.
    === {wide_contents} ===
    Please translate only the next sentences into {language}'
    <{target_content}>"""
    return text


class BookTranslater(Book, LLM):
    def __init__(self, book, model, translate_base_language = None ,target_language="jp"):
        self.book = book
        self.model = model
        if translate_base_language:
            self.input_language = translate_base_language
        else:
            self.input_language = book.base_language
        self.target_language = target_language
        self.book_token_count()

    def book_token_count(self) -> None:
        for line in self.book.lines:
            line.token_count(self.model.name, self.input_language) = self.model.count_tokens(line.contents)

    def make_prompt_with_line(self, line: Line) -> Prompt:
        return self.build_single_line_translate_prompt(line)

    def make_prompt_with_lines(self, lines: list[Line], index = 0) -> tuple[list[Prompt],int]:
        text = self.multi_line_translate_prompt(lines)
        if index > len(lines):
            raise ValueError(f"we cann't translate any of this line {lines}")
        if self.is_able_translate_all_words(self.model.count_tokens(text)):
            return [text], index
        else:
            prompt, index = make_prompt_with_lines(lines[:-index], index+1)






        # else:
        #     msg = "The line is too long to translate."
        #     raise ValueError(msg)

    def find_target_list(self, components: list[TextComponent], lack_of_token:int) -> tuple[list[TextComponent], list[TextComponent]]:
        reversed_components = components[::-1]
        for remove_index, remove_content in enumerate(reversed_components):
            lack_of_token += remove_content.token_count
            if lack_of_token:
                return components[:-remove_index], components[-remove_index:]
        raise ValueError("we can't find the target index.")

    def make_prompt_with_text_component(self, component: TextComponent) -> list[Prompt]:
        # when next atom is line.
        if isinstance(component.contents[0], Line) and len(component.contents) <= 1:
            prompt = self.make_prompt_with_line(component.contents[0])
            if self.calc_affoadable_text_count(self.model.count_tokens(prompt)):
                return prompt

        if isinstance(component.contents[0], Line):
            prompts, index = self.make_prompt_with_lines(component.contents)  # type: ignore

            if self.calc_affoadable_text_count(self.model.count_tokens(prompt.)):
                return prompt

        if self.is_able_translate_all_words(component.token_count):
            return [self.multi_line_translate_prompt(component.lines)]
        input_afford, outupt_afford = self.calc_affoadable_text_count(component.token_count)
        result = []
        if input_afford < 0:
            # total input is too big and each input is too big.
            if len(component.contents) <= 1:
                return self.make_prompt_with_text_component(component.contents[0])
            result.extend(self.make_prompt_with_list(component.contents[:])) # type: ignore
        if outupt_afford < 0:


        # def make_context_with_output_limit(self, total_lines, target_lines) -> list[Prompt]:


            # if not self.is_able_translate_all_words(component.contents[0].token_count):
            #     result.extend(self.make_prompt_with_text_component(component.contents[0]))
            #     result.extend(self.make_prompt_with_list(component.contents[1:])) # type: ignore
            #     return result
            # # total input is too big and each input is small, so separate components.
            # calcable_components, removed_components = self.find_target_list(component.contents, input_afford)
            # result.extend(self.make_prompt_with_list(calcable_components))
            # result.extend(self.make_prompt_with_list(removed_components))

    def make_prompt(self, content: TextComponent | Line) -> list[Prompt]:
        if isinstance(content, Line):
            return self.make_prompt_with_line(content)
        else:
            return self.make_prompt_with_text_component(content)

    def make_prompt_with_list(self, contents: list[TextComponent]) -> list[Prompt]:
        local_tokens = 0
        next_local_tokens = 0
        local_lines = []
        for content in contents:
            next_local_tokens = content.token_count + local_tokens
            if self.is_able_translate_all_words(next_local_tokens):
                local_lines.append(content.lines)
                continue
            else:
                if local_tokens == 0:
                    # separate the content into small one.

    def calc_prompt_input_size_afford(self, prompt_or_token: Prompt | int) -> int:
        if isinstance(prompt_or_token, Prompt):
            return self.model.input_token_limit - self.model.count_tokens(prompt_or_token.script)
        return self.model.input_token_limit - prompt_or_token

    def calc_prompt_output_size_afford_in_base(self, prompt_or_token: Prompt | int) -> int:
        if self.input_language == "en" and self.target_language == "jp":
            rate = self.en_to_jp
        elif self.input_language == "jp" and self.target_language == "en":
            rate = self.jp_to_en
        else:
            raise ValueError("The language is not supported.")
        if isinstance(prompt_or_token, Prompt):
            return self.output_token_limit // rate - self.model.count_tokens(prompt_or_token.raw_lines)
        return self.model.input_token_limit // rate - prompt_or_token

    def is_able_translate_all_words(self, prompt_or_token: Prompt|int) -> bool:
        return self.calc_prompt_input_size_afford(prompt_or_token) >= 0 and self.calc_prompt_output_size_afford_in_base(prompt_or_token) >= 0

    def call_llm(self, text: str) -> str:
        result = ""
        response = self.model.generate_content(text)
        for chunk in response:
            result += chunk.text
        return result

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
