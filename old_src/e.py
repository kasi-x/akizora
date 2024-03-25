from urllib.request import urlopen

from bs4 import BeautifulSoup as bs

url = "https://www.aozora.gr.jp/cards/000074/files/427_19793.html"

with urlopen(url) as response:
    soup = bs(response, "html.parser")

# "title"クラスを持つh1タグのテキストを取得
title = (
    soup.select_one("h1.title").get_text(strip=True)
    if soup.select_one("h1.title")
    else "タイトルが見つかりません"
)

# "author"クラスを持つh2タグのテキストを取得
author = (
    soup.select_one("h2.author").get_text(strip=True)
    if soup.select_one("h2.author")
    else "著者が見つかりません"
)

# "main_text"クラスを持つdivタグからテキストを取得
# ここでのCSSセレクタは直接的なクラス名を利用しています。
main_text_div = soup.select_one("div.main_text")
if main_text_div:
    # 不要なタグ "rp" と "rt" を削除
    for tag in main_text_div.find_all(["rp", "rt"]):
        tag.decompose()
    main_text = main_text_div.get_text(strip=True)
else:
    main_text = "本文が見つかりません"

# 結果を表示
print("Title:", title)
print("Author:", author)
print("Main Text:", main_text[:1000], "...")  # 本文が長いため、最初の1000文字のみ表示

with open("main_text.txt", "w") as file:
    file.write(main_text)
