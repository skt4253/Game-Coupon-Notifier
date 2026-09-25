import os, re, requests
from datetime import datetime, timezone, timedelta

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]

TIMEOUT = 20
MAX_BUTTONS = 25   # 디스코드 메시지당 버튼 최대 개수 (한 줄 5개 × 5줄)
FIELD_LIMIT = 1024 # 임베드 필드 값 최대 길이

# (환경변수, 게임 이름, 버튼용 짧은 이름, 교환 URL)
GAMES = [
    ("GENSHIN", "원신",          "원신",   "https://genshin.hoyoverse.com/ko/gift?code={}"),
    ("HSR",     "붕괴 스타레일",  "스레",   "https://hsr.hoyoverse.com/gift?code={}"),
    ("ZZZ",     "젠레스 존 제로", "젠존제", "https://zenless.hoyoverse.com/redemption?code={}"),
]

def parse_codes(s):
    # 공백/쉼표로 나누고 대문자로 변환, 입력 순서를 유지하며 중복 제거
    if not s:
        return []
    return list(dict.fromkeys(c.upper() for c in re.split(r"[\s,]+", s) if c))

def make_fields(name, lines):
    # 필드 값이 1024자를 넘으면 "(계속)" 필드로 나눔
    fields, chunk = [], ""
    for line in lines:
        if chunk and len(chunk) + 1 + len(line) > FIELD_LIMIT:
            fields.append({"name": name, "value": chunk, "inline": False})
            name, chunk = f"{name} (계속)", ""
        chunk = f"{chunk}\n{line}" if chunk else line
    if chunk:
        fields.append({"name": name, "value": chunk, "inline": False})
    return fields

def build_message():
    fields, buttons, overflow = [], [], False

    for env, name, short, url in GAMES:
        codes = parse_codes(os.environ.get(env, ""))
        if not codes:
            continue
        print(f"[DEBUG] {name}: {', '.join(codes)}")
        fields += make_fields(name, [f"[{c}]({url.format(c)})" for c in codes])
        for c in codes:
            if len(buttons) >= MAX_BUTTONS:
                overflow = True
                break
            buttons.append({"type": 2, "style": 5, "label": f"{short} {c}"[:80], "url": url.format(c)})

    if not fields:
        return None

    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    embed = {"title": "🎁 쿠폰 교환 링크", "color": 0x5865F2, "fields": fields,
             "footer": {"text": now}}
    if overflow:
        embed["footer"]["text"] += f" · 버튼은 최대 {MAX_BUTTONS}개까지 표시됩니다. 나머지는 위 링크를 이용하세요."

    rows = [{"type": 1, "components": buttons[i:i + 5]} for i in range(0, len(buttons), 5)]
    return {"embeds": [embed], "components": rows}

def send_discord(payload):
    # 일반 웹훅은 with_components=true 를 붙여야 링크 버튼이 표시됨
    try:
        r = requests.post(DISCORD_WEBHOOK, params={"with_components": "true"}, json=payload, timeout=TIMEOUT)
        if not r.ok:
            print(f"[WARN] 디스코드 전송 실패: HTTP {r.status_code} {r.text[:200]}")
            return False
    except Exception as e:
        print(f"[WARN] 디스코드 전송 실패: {type(e).__name__}")
        return False
    return True

if __name__ == "__main__":
    payload = build_message()
    if payload is None:
        print("❌ 코드를 하나 이상 입력해 주세요.")
        raise SystemExit(1)
    if not send_discord(payload):
        raise SystemExit(1)
    print("✅ 쿠폰 교환 링크 전송 완료")
