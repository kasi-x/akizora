def bookInfo(book_id):
    import requests
    from bs4 import BeautifulSoup

    res = requests.get(f"http://pubserver2.herokuapp.com/api/v0.1/books/{book_id}/content?format=html")

    soup = BeautifulSoup(res.text, "html.parser")
    for tag in soup.find_all(["rt", "rp"]):
        tag.decompose() # タグとその内容の削除

    if (soup.find("title") is None) or (soup.find("div") is None) or (soup.find("div", {"class": "main_text"}) is None):
        return [book_id, "", "", "", ""]
    else:
        title =  soup.find("title").get_text()
        title_list = title.split(" ")
        book_author = title_list[0] # 著者名
        book_title = title_list[1] # タイトル
        book_title_info = len(title_list) > 2 # タイトルが途切れているか

        print(soup.find("div", {"class": "main_text"}))
        text_list = soup.find("div", {"class": "main_text"}).get_text().strip("\r\n\u3000").split("。")
        text_first = text_list[0] + "。" if (len(text_list[0]) < 100) else "too long" #　冒頭
        else:
            text_last = ""

        list = [book_id, book_author, book_title, book_title_info, text_first]
        print(list)
        return list
