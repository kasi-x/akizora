from abc import ABC
from abc import abstractmethod
from enum import Enum

import google.generativeai as genai

type TOKEN_COSTS_TABLE = dict[Language, int]


class Language(Enum):
    # ISO 639-3
    jpn = "Japanese"
    eng = "English"  # US English vs UK English
    undifined = "undifined"


GEMINI_TOKEN_COST_TABLE: TOKEN_COSTS_TABLE = {
    # the amount is all of translate costs by english.
    Language.jpn: 5,
    Language.eng: 1,
}


class LLM_TYPE(Enum):
    GEMINI_PRO = "gemini-pro"
    GPT3 = "gpt3"


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
    def calc_tokens(self, text: str) -> int:
        print("Not implemented yet")
        return -1

    def calc_token_rate(self, from_language: Language, to_language: Language) -> int:
        return self.token_cost_table[to_language] // self.token_cost_table[from_language]

    def is_output_token_affording(self, input_token, from_language, to_language) -> bool:
        return self.output_token_limit >= input_token * self.calc_token_rate(
            from_language, to_language
        )

    def is_input_token_affording(self, input_token) -> bool:
        return self.input_token_limit >= input_token


class GEMINI_PRO(LLM):
    def __init__(self):
        super().__init__(
            name=LLM_TYPE.GEMINI_PRO,
            input_token_limit=30720,
            output_token_limit=2048,
            token_cost_table=GEMINI_TOKEN_COST_TABLE,
        )
        self.model = genai.GenerativeModel("gemini-pro")

    def call_llm(self, text: str) -> str:
        result = ""
        response = self.model.generate_content(text)
        for chunk in response:
            result += chunk.text
        return result

    def calc_tokens(self, text: str) -> int:
        if not text:
            print("text is empty")
            return 0
        result = self.model.count_tokens(text)
        # sleep(0.1)
        if isinstance(result, int):
            return result
        return result.total_tokens


def call_gemini():
    return GEMINI_PRO()


class GPT(LLM):
    def __init__(self):
        pass  # TODO: Implement GPT's Translator

    def call_llm(self, text: str) -> str:
        return f"{text} inputed, but not implemented"

    def calc_tokens(self, text: str) -> int:
        # TODO: Implement GPT's count_llm_tokens
        return 0
