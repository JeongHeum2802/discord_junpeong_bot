# Discord 메시지 길이 제한 처리용 유틸
# 청크단위로 메시지를 쪼개준다

def split_message(text: str, max_length: int = 1900) -> list[str]:
    chunks = []

    while len(text) > max_length:
        split_index = text.rfind("\n", 0, max_length)

        if split_index == -1:
            split_index = max_length

        chunks.append(text[:split_index])
        text = text[split_index:].lstrip()

    if text:
        chunks.append(text)

    return chunks