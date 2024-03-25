from urllib.request import urlopen

from bs4 import BeautifulSoup as bs

url = "https://www.aozora.gr.jp/cards/000074/files/427_19793.html"

with urlopen(url) as response:
    soup = bs(response, "html.parser")

main_text_div = soup.find("div", class_="main_text")

for tag in main_text_div.find_all(["rp", "rt"]):
    tag.decompose()

cleaned_text = main_text_div.get_text()

print(cleaned_text)
