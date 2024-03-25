text = "<BODY:2>placeholder1<PROLOGUE:5><PROLOGUE_TITLE:4>placeholder2</PROLOGUE_TITLE:4>placeholder3<BODY:2>placeholder4<CHAPTER:3><CHAPTER_TITLE:2>placeholder5</CHAPTER_TITLE:2>placeholder6<BODY:2>placeholder7<CHAPTER:3><CHAPTER_TITLE:2>placeholder8</CHAPTER_TITLE:2>placeholder9<BODY:2>placeholder10<EPILOGUE:5>placeholder11<BODY:2>placeholder12<THE_END:6>placeholder13</THE_END:6>placeholder14<BODY:2>placeholder15<TRANSCRIBER_NOTES:5>placeholder16<BODY:2>placeholder17"

import re

tag_or_placeholder_pattern = re.compile(r"<(/?)(\w+)(\d*):?(\d*)>|placeholder\d+")

stack: list[tuple[str, int]] = []
result: list[str] = []


def should_insert_stack(stack, new_tag_priority):
    if not stack:
        return True
    return stack[-1][1] <= new_tag_priority


for match in tag_or_placeholder_pattern.finditer(text):
    is_place_holder = "placeholder" in match.group(0)
    if is_place_holder:
        result.append(match.group(0))
    else:
        tag_type = "/" if match.group(1) else "Opening"
        tag_name = match.group(2)
        tag_priority_str = match.group(3) or match.group(4)
        tag_priority = int(tag_priority_str) if tag_priority_str.isdigit() else -1

        if tag_type == "Opening":
            while stack and should_insert_stack(stack, tag_priority):
                tag = stack.pop()
                result.append(f"</{tag[0]}:{tag[1]}>")
            stack.append((tag_name, tag_priority))
            result.append(f"<{tag_name}:{tag_priority}>")
            print(f"stack: {stack}")
        else:
            while stack:
                tag = stack.pop()
                result.append(f"</{tag[0]}:{tag[1]}>")
                if tag[0] == tag_name:
                    break
            print(f"stack: {stack}")
while stack:
    tag = stack.pop()
    result.append(f"</{tag[0]}:{tag[1]}>")


import re

tag_pattern = re.compile(r"<(/?)(\w+):?(\d*)>")
stack = []
result = []
last_pos = 0

for match in tag_pattern.finditer(text):
    start_position, end_position = match.span()
    tag_type, tag_name, tag_priority_str = match.groups()
    tag_priority = int(tag_priority_str) if tag_priority_str else 0

    # if tag_type == "/":
    if not stack and not tag_type:
        stack.append((tag_name, tag_priority))
        continue

    if tag_type == "/":
        while stack:
            open_tag_name, open_tag_priority = stack.pop()
            if open_tag_name == tag_name:
                break
            result.append(f"</{open_tag_name}:{open_tag_priority}>")

    # Add text before the current tag
    # result.append(text[last_pos:start])
    # last_pos = end
    #
    # if tag_type == "/":  # Closing tag
    #     # Pop until we find the matching opening tag
    #     while stack:
    #         open_tag_name, open_tag_priority, open_tag_start = stack.pop()
    #         if open_tag_name == tag_name:
    #             break
    #         # Add missing closing tags for unclosed tags
    #         result.insert(open_tag_start, f"</{open_tag_name}:{open_tag_priority}>")
    # else:  # Opening tag
    #     stack.append((tag_name, tag_priority, len("".join(result))))
    #
    # # Add the current tag to the result
    # result.append(match.group(0))

# Add the remaining text after the last tag
result.append(text[last_pos:])

# Close any remaining unclosed tags
for open_tag_name, open_tag_priority, open_tag_start in reversed(stack):
    result.insert(open_tag_start, f"</{open_tag_name}:{open_tag_priority}>")

print("".join(result))
