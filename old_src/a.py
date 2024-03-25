import io

from lxml import html

file_path = "./1567_14913.html"

# HTMLファイルをバイト列として読み込む
with open(file_path, "rb") as file:
    html_content = file.read()

# UTF-8でデコードし、ASCIIにエンコードする
# ここでは、HTMLファイルが基本的にUTF-8であることを前提としていますが、
# 実際のエンコーディングに応じて適宜調整してください。
html_content = html_content.decode("utf-8").encode("ascii", "xmlcharrefreplace")

# HTMLコンテンツをパース
doc = html.fromstring(html_content)

# XPathを使用して特定のテキストを抽出（例としてタイトルと著者を取得）
title = doc.xpath('//h1[@class="title"]/text()')
author = doc.xpath('//h2[@class="author"]/text()')

# 結果を出力
print("Title:", title)
print("Author:", author)
