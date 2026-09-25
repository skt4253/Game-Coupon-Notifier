"""봇과 웹훅이 함께 쓰는 쿠폰 코드 처리 로직."""

import re

# key: (게임 이름, 짧은 이름, 교환 URL 템플릿)
GAMES = {
    "genshin": ("원신", "원신", "https://genshin.hoyoverse.com/ko/gift?code={}"),
    "hsr": ("붕괴: 스타레일", "스레", "https://hsr.hoyoverse.com/gift?code={}"),
    "zzz": ("젠레스 존 제로", "젠존제", "https://zenless.hoyoverse.com/redemption?code={}"),
}

TITLE = "🎁 쿠폰 교환 링크"
COLOR = 0x5865F2
EMPTY_MESSAGE = "코드를 하나 이상 입력해 주세요."
MAX_BUTTONS = 25
FIELD_LIMIT = 1024
LABEL_LIMIT = 80


def parse(s: str | None) -> list[str]:
    """공백/쉼표로 나누고 대문자로 바꾼 뒤, 입력 순서를 유지하며 중복을 제거합니다."""
    if not s:
        return []
    return list(dict.fromkeys(c.upper() for c in re.split(r"[\s,]+", s) if c))


def build(inputs: dict[str, str | None]) -> tuple[list[tuple[str, str]], list[tuple[str, str]], bool]:
    """게임별 입력을 받아 (임베드 필드, 버튼, 버튼 초과 여부)를 돌려줍니다.

    필드는 (이름, 값), 버튼은 (라벨, URL) 튜플입니다.
    필드 값이 1024자를 넘으면 "(계속)" 필드로 나눕니다.
    """
    fields: list[tuple[str, str]] = []
    buttons: list[tuple[str, str]] = []
    overflow = False

    for key, raw in inputs.items():
        codes = parse(raw)
        if not codes:
            continue
        name, short, url = GAMES[key]

        chunk = ""
        for c in codes:
            line = f"[{c}]({url.format(c)})"
            if chunk and len(chunk) + 1 + len(line) > FIELD_LIMIT:
                fields.append((name, chunk))
                name, chunk = f"{name} (계속)", ""
            chunk = f"{chunk}\n{line}" if chunk else line
        fields.append((name, chunk))

        for c in codes:
            if len(buttons) >= MAX_BUTTONS:
                overflow = True
                break
            buttons.append((f"{short} {c}"[:LABEL_LIMIT], url.format(c)))

    return fields, buttons, overflow


def overflow_footer() -> str:
    return f"버튼은 최대 {MAX_BUTTONS}개까지 표시됩니다. 나머지는 위 링크를 이용하세요."
