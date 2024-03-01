import re


def auto_close_tags(text):
    # FUTURE: expand this priority later.
    """Maybe more priority is required later and in some special book.
    this priority is just for idea for me.
    for example, PART vs EPIOLOGUE, which is more important?
    In some book, each part has epilogue, so PART can be more important.
    """
    priority = {
        "PART": 3,
        "CHAPTER": 2,
        "TRANSCRIBER_NOTES": 4,
        "THE_END": 4,
        "EPILOGUE": 4,
        "PROLOGUE": 4,
        "DATA": 1,
    }
    priority = dict(sorted(priority.items(), key=lambda item: item[1]))

    def sort_tags(tags):
        return sorted(tags, key=lambda tag: priority.get(tag, -1))

    def get_priority(tag):
        return priority.get(tag, -1)

    # Not yet used que. But you should change this to que.
    living_tag_stack = []
    contents = []
    remove_list = []

    tag_pattern = re.compile(r"</?([A-Z_]+)>")

    lines = text.split("\n")

    # REFACTOR: make more readable this function by separating into functions.
    for line in lines:
        tags_found = tag_pattern.findall(line)
        for new_tag in tags_found:
            start_tag = f"<{new_tag}>"
            end_tag = f"</{new_tag}>"
            if start_tag in line:
                if living_tag_stack:
                    for open_tag in living_tag_stack:
                        if get_priority(open_tag) <= get_priority(new_tag):
                            # OPTIMIZE: rewrite for change algorithm.
                            """Use stack and pop and change this algorithm.
                            We can use html tag relate idea. Never happen '<t><a> </t></a>', close tag must be in order.
                            In other words, when stack is '<chapter><hoge>' and </chapeter> event happend, <hoge> must be closed at previous point of close chapter.
                            Be careful to keep passing test case.
                            """

                            contents.append(f"</{open_tag}>")
                            remove_list.append(open_tag)
                    living_tag_stack = [
                        new_tag for new_tag in living_tag_stack if new_tag not in remove_list
                    ]
                    remove_list = []
                living_tag_stack.append(new_tag)
                living_tag_stack = sort_tags(living_tag_stack)

            if end_tag in line:
                living_tag_stack.remove(new_tag)
                if living_tag_stack:  # POINTLESS: not required. Because for loop is not executed when living_tag_stack is empty.
                    for open_tag in living_tag_stack:
                        if get_priority(open_tag) <= get_priority(new_tag):
                            contents.append(f"</{open_tag}>")
                            remove_list.append(open_tag)
                    living_tag_stack = [
                        new_tag for new_tag in living_tag_stack if new_tag not in remove_list
                    ]
                    remove_list = []
        contents.append(line)

    while living_tag_stack:
        contents.append(f"</{living_tag_stack.pop()}>")

    return "\n".join(contents)
