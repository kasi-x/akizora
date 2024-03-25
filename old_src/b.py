from lxml import html

file_path = "./1567_14913.html"

# HTMLファイルをバイト列として読み込む
with open(file_path, "rb") as file:
    html_content = file.read()

# HTMLコンテンツをパース
doc = html.fromstring(html_content)

# 指定されたXPathに一致する要素の内容を取得
# XPathのインデックスは1から始まるため、div[3]は3番目のdiv要素を指します。
target_element = doc.xpath("/html/body/div[3]")

# 抽出された要素が存在する場合、その内容を表示
if target_element:
    content = html.tostring(target_element[0], pretty_print=True).decode("utf-8")
    print(content)
else:
    print("指定されたXPathに一致する要素が見つかりませんでした。")
