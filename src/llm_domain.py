from abc import ABC
from abc import abstractmethod
from enum import Enum
from time import sleep
from typing import Literal

import google.generativeai as genai

type TOKEN_COSTS_TABLE = dict[LanguageEnum, int]

type Language = Literal["Japanese", "English"]
type LLM_TYPE_NAME = str


class LanguageEnum(Enum):
    # ISO 639-3
    jpn = "Japanese"
    eng = "English"  # US English vs UK English
    undifined = "undifined"


GEMINI_TOKEN_COST_TABLE: TOKEN_COSTS_TABLE = {
    # the amount is all of translate costs by english.
    LanguageEnum.jpn: 5,
    LanguageEnum.eng: 1,
}


class LLM(ABC):
    def __init__(self, name, input_token_limit, output_token_limit, token_cost_table):
        self.name: LLM_TYPE_NAME = name
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
            name="gemini-pro",
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
            print(f"failed with : {text}")
            return 0

        return self.model.count_tokens(text).total_tokens


def call_gemini():
    return GEMINI_PRO()


class GPT(LLM):
    def __init__(self):
        pass  # TODO: Implement GPT's Translator

    def call_llm(self, text: str) -> str:
        return f"{text} inputed, but not implemented"

    def calc_tokens(self) -> int:
        # TODO: Implement GPT's count_llm_tokens
        return 0
