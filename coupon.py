import os, re, json, requests
from datetime import datetime, timezone, timedelta

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]

TIMEOUT = 20
MAX_BUTTONS = 25   # 디스코드 메시지당 버튼 최대 개수 (한 줄 5개 × 5줄)
FIELD_LIMIT = 1024 # 임베드 필드 값 최대 길이
SENT_FILE = "sent.json"  # 이미 보낸 코드 기록

# 외부에서 가져온 값은 이 형식에 맞는 코드만 사용 (링크/마크다운 주입 방지)
CODE_RE = re.compile(r"^[A-Z0-9]{4,30}$")

# 웹 교환 페이지가 없는 게임(명조)은 코드와 함께 이 안내를 보여 줌
WUWA_GUIDE = "게임 내 터미널 → 설정 → 기타 설정 → 교환 코드에 입력하세요."

def parse_codes(s):
    # 공백/쉼표로 나누고 대문자로 변환, 입력 순서를 유지하며 중복 제거
    if not s:
        return []
    return list(dict.fromkeys(c.upper() for c in re.split(r"[\s,]+", s) if c))

def clean_rewards(s):
    # "Primogem*60;Mora*20000" → "Primogem×60, Mora×20000", 마크다운/멘션에 쓰이는 문자 제거
    s = (s or "").replace("*", "×").replace(";", ", ").replace("_", " ")
    s = re.sub(r"[^\w\s,.'’×+\-]", "", s)  # URL·마크다운·멘션에 쓰이는 문자 제거
    return re.sub(r"\s+", " ", s).strip()[:150]

# ---------- 수집 ----------

def fetch_seria(game):
    # 비공식 공개 API: https://hoyo-codes.seria.moe
    r = requests.get("https://hoyo-codes.seria.moe/codes", params={"game": game}, timeout=TIMEOUT)
    r.raise_for_status()
    return [(c.get("code", ""), c.get("rewards", "")) for c in r.json().get("codes", []) if c.get("status") == "OK"]

def fetch_hoyolab(game_id):
    # HoYoLAB 게임 가이드 페이지의 교환 코드 모듈 (방송 코드가 있을 때만 채워짐)
    r = requests.get("https://bbs-api-os.hoyolab.com/community/painter/wapi/circle/channel/guide/material",
                     params={"game_id": game_id}, headers={"x-rpc-language": "ko-kr"}, timeout=TIMEOUT)
    r.raise_for_status()
    codes = []
    for m in (r.json().get("data") or {}).get("modules") or []:
        for b in (m.get("exchange_group") or {}).get("bonuses") or []:
            codes.append((b.get("exchange_code", ""), ""))
    return codes

MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July",
                                      "August", "September", "October", "November", "December"], 1)}

def fetch_wuwa_wiki(_):
    # 명조 Fandom 위키의 Redemption Code 문서 중 Active 표. 위키 갱신이 늦어 만료일로 한 번 더 거름
    r = requests.get("https://wutheringwaves.fandom.com/api.php",
                     params={"action": "parse", "page": "Redemption_Code", "prop": "wikitext", "format": "json"},
                     headers={"User-Agent": "Hoyo-Coupon-Link (GitHub Actions)"}, timeout=TIMEOUT)
    r.raise_for_status()
    text = r.json()["parse"]["wikitext"]["*"]
    active = text.split("===Active===", 1)[1].split("===", 1)[0]

    now = datetime.now(timezone(timedelta(hours=-8)))  # 위키 만료 시각은 PT 기준 (PST로 넉넉하게)
    codes = []
    for row in active.split("\n|-"):
        code = re.search(r"<code>(.+?)</code>", row)
        if not code:
            continue
        until = re.search(r"Valid until: ([A-Z][a-z]+) (\d{1,2}), (\d{4})(?: (\d{1,2}):(\d{2}))?", row)
        if until and until.group(1) in MONTHS:
            mon, day, year = MONTHS[until.group(1)], int(until.group(2)), int(until.group(3))
            hh, mm = (int(until.group(4)), int(until.group(5))) if until.group(4) else (23, 59)
            if now > datetime(year, mon, day, hh, mm, tzinfo=now.tzinfo):
                continue
        rewards = re.search(r"Card List\|(.*?)\|delim", row)
        codes.append((code.group(1), rewards.group(1) if rewards else ""))
    return codes

# (키, 수동 입력 환경변수, 게임 이름, 버튼용 짧은 이름, 교환 URL(없으면 None), 수집처 [(이름, 함수, 인자)])
GAMES = [
    ("genshin", "GENSHIN", "원신",          "원신",   "https://genshin.hoyoverse.com/ko/gift?code={}",
     [("seria", fetch_seria, "genshin"), ("hoyolab", fetch_hoyolab, 2)]),
    ("hsr",     "HSR",     "붕괴 스타레일",  "스레",   "https://hsr.hoyoverse.com/gift?code={}",
     [("seria", fetch_seria, "hkrpg"),   ("hoyolab", fetch_hoyolab, 6)]),
    ("zzz",     "ZZZ",     "젠레스 존 제로", "젠존제", "https://zenless.hoyoverse.com/redemption?code={}",
     [("seria", fetch_seria, "nap"),     ("hoyolab", fetch_hoyolab, 8)]),
    ("wuwa",    "WUWA",    "명조",          "명조",   None,
     [("wiki", fetch_wuwa_wiki, None)]),
]

def collect(sources, name):
    # 코드 → 보상. 한 수집처가 실패해도 나머지로 계속 진행
    found = {}
    for label, fetch, arg in sources:
        try:
            items = fetch(arg)
        except Exception as e:
            print(f"[WARN] {name} {label} 수집 실패: {type(e).__name__}")
            continue
        for code, rewards in items:
            code = str(code).strip().upper()
            if CODE_RE.match(code):
                found[code] = found.get(code) or clean_rewards(str(rewards))
        print(f"[DEBUG] {name} {label}: {len(items)}개")
    return found

# ---------- 기록 ----------

def load_sent():
    try:
        with open(SENT_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_sent(sent):
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(sent, f, ensure_ascii=False, indent=2)
        f.write("\n")

# ---------- 디스코드 ----------

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

def build_message(title, per_game):
    # per_game: [(게임 이름, 짧은 이름, 교환 URL 또는 None, {코드: 보상})]
    fields, buttons, overflow = [], [], False

    for name, short, url, codes in per_game:
        if not codes:
            continue
        if url is None:
            # 웹 교환 페이지가 없으면 복사하기 쉬운 코드 블록 + 입력 위치 안내, 버튼 없음
            lines = [f"`{c}`" + (f" · {r}" if r else "") for c, r in codes.items()]
            fields += make_fields(name, lines + [f"*{WUWA_GUIDE}*"])
            continue
        lines = [f"[{c}]({url.format(c)})" + (f" · {r}" if r else "") for c, r in codes.items()]
        fields += make_fields(name, lines)
        for c in codes:
            if len(buttons) >= MAX_BUTTONS:
                overflow = True
                break
            buttons.append({"type": 2, "style": 5, "label": f"{short} {c}"[:80], "url": url.format(c)})

    if not fields:
        return None

    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    embed = {"title": title, "color": 0x5865F2, "fields": fields, "footer": {"text": now}}
    if overflow:
        embed["footer"]["text"] += f" · 버튼은 최대 {MAX_BUTTONS}개까지 표시됩니다. 나머지는 위 링크를 이용하세요."

    payload = {"embeds": [embed], "allowed_mentions": {"parse": []}}
    if buttons:
        payload["components"] = [{"type": 1, "components": buttons[i:i + 5]} for i in range(0, len(buttons), 5)]
    return payload

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

# ---------- 실행 ----------

if __name__ == "__main__":
    sent = load_sent()
    manual = any(os.environ.get(env, "").strip() for _, env, *_ in GAMES)

    per_game, new_sent = [], {}
    for key, env, name, short, url, sources in GAMES:
        if manual:
            # 수동 입력: 이미 보낸 코드라도 그대로 보냄
            codes = {c: "" for c in parse_codes(os.environ.get(env, ""))}
        else:
            # 자동 수집: 아직 보내지 않은 코드만
            codes = {c: r for c, r in collect(sources, name).items() if c not in sent.get(key, [])}
        if codes:
            print(f"[DEBUG] {name} 전송 대상: {', '.join(codes)}")
        per_game.append((name, short, url, codes))
        new_sent[key] = sent.get(key, []) + [c for c in codes if c not in sent.get(key, [])]

    title = "🎁 쿠폰 교환 링크" if manual else "🎁 새 쿠폰 교환 링크"
    payload = build_message(title, per_game)
    if payload is None:
        print("☑️ 새 코드 없음")
        raise SystemExit(0)
    if not send_discord(payload):
        raise SystemExit(1)
    save_sent(new_sent)
    print("✅ 쿠폰 교환 링크 전송 완료")
