import pathlib
import textwrap

import google.generativeai as genai
from dotenv import load_dotenv

# from IPython.display import Markdown
# from IPython.display import display

load_dotenv("GOOGLE_API_KEY")

model = genai.GenerativeModel("gemini-pro")

# response = model.generate_content("What is the meaning of life?")
#
# # print(response.text)
# try:
#     print(response.text)
# except Exception as e:
#     print(f"{type(e).__name__}: {e}")


def count_tokens(text):
    tokenizer = model.count_tokens(text)
    print(tokenizer)

    # トークンの数を返す


count_tokens("Hello, world!")

# genai.configure(api_key=GOOGLE_API_KEY)
