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

# 보상 아이템 한국어 이름 (게임 데이터 기준, 영어 이름은 소문자로 비교)
ITEM_KO = {
    # 원신
    "adventurer's experience": "모험가의 경험",
    "broken drive shaft": "훼손된 구동축",
    "chenyu adeptea": "침옥 선잎",
    "crepes suzette": "크레프 쉬제트",
    "fine enhancement ore": "정제용 광물",
    "fruit tandem turnovers": "과일 듀엣 롤",
    "hero's wit": "영웅의 경험",
    "jueyun chili chicken": "절운고추 치킨",
    "long night alight": "긴 밤의 불꽃",
    "midsommar torte": "여름빛 참나무 케이크",
    "moonfall silver": "달빛 은",
    "mora": "모라",
    "mystic enhancement ore": "정제용 마법 광물",
    "primogem": "원석",
    "stir-fried fish noodles": "생선 볶음면",
    "tattered warrant": "마모된 표장",
    "tea break pancake": "장원 팬케이크",
    "teachings of freedom": "「자유」의 가르침",
    "teachings of moonlight": "「달빛」의 가르침",
    "teyvat fried egg": "티바트 달걀 프라이",
    "varunada lazurite sliver": "순수한 청금석 가루",
    "vayuda turquoise sliver": "자유로운 터키석 가루",
    # 붕괴 스타레일
    "adventure log": "모험 기록",
    "alfalfa salad": "알팔파 샐러드",
    "amber huadiao wine": "호박(琥珀) 화조주",
    "antimatter field generator": "반물질 역장 생성기",
    "automatic wooden dummy": "자동 목인장",
    "badge battle robe": "캔배지 전투복",
    "banasocial etiquette": "나나 에티켓",
    "berrypheasant skewers": "열매공작 꼬치",
    "bottled soda": "해피 워터",
    "camo paint": "위장 페인트",
    "chrysos heir dolium": "황금의 후예 질항아리",
    "classic soulglad": "클래식 솔글래드",
    "condensed aether": "응축한 에테르",
    "cosmic fried rice": "대우주 볶음밥",
    "credit": "신용 포인트",
    "crystal lizard satay": "보석 도마뱀 꼬치",
    "dazzling ninja provisions": "요란 인법 군량",
    "disposable shield": "일회용 보호벽",
    "dream syrup": "좋은꿈 시럽",
    "dreamville special": "좋은꿈 마을 스페셜 블렌드",
    "dry emergency light": "건식 비상등",
    "dust of alacrity": "재빠른 먼지",
    "energy drink": "에너지 음료",
    "express special blend: rustic infusion": "열차 스페셜 블렌드: 땔감, 쌀 그리고 소금",
    "firmament note": "구름 위 음표",
    "five-grain jade elixir": "오곡즙",
    "flaming potent tea": "화염차",
    "fuel": "연료",
    "full-auto dreampaint spray": "전자동 꿈 그리기 스프레이",
    "golden honeycake": "황금 허니 팬케이크",
    "golden slumbernana": "황금빛 졸리나나",
    "grande rejuvepill": "대환단",
    "halovian winged burger": "헤일로 윙 버거",
    "health detox pill": "기황해독환",
    "high-tech protective gear": "첨단 방어구",
    "hypnotic hammer": "수면 망치",
    "immortal's delight": "선인의 기쁨차",
    "jade marrow diffusion": "옥수풍골산",
    "life transmitter": "생명 전송기",
    "lost crystal": "유실된 수정덩이",
    "lost gold fragment": "유실된 황금 파편",
    "oak cake rolls": "참나무 롤케이크",
    "odd gummy candy": "이상한 소프트 캔디",
    "pika white grape soda": "피카 백포도 소다수",
    "pom-pom's fried fowl": "폼폼 특제 후라이드",
    "potato fries sundae": "감자튀김 선디",
    "reduce bananxiety": "걱정하지 말게나나",
    "refined aether": "정제한 에테르",
    "rejuvenation pellet": "양심반혼단",
    "rough sketch": "거친 스케치",
    "scalegorge spring water": "인연 얼음샘",
    "scare box": "깜짝 상자",
    "signature chili oil beef offal stew": "대표 메뉴 고추기름 난도질 소내장탕",
    "songlotus cake": "연근떡",
    "sparse aether": "희박한 에테르",
    "startaro bubble": "별타로 버블티",
    "steamed puffergoat milk": "따끈 양유",
    "steelclaw dagger": "강철 발톱 비수",
    "stellar jade": "성옥",
    "stone from the everwinter monument": "영원한 겨울의 비석",
    "sweet dreams holographic ticket": "좋은꿈 홀로그램 티켓",
    "sweet dreams soda": "단꿈 소다수",
    "travel encounters": "여행 견문",
    "traveler's guide": "여행 가이드",
    "trick snack": "특이한 간식",
    # 젠레스 존 제로
    "bangboo algorithm module": "「Bangboo」 알고리즘 모듈",
    "denny": "데니",
    "official investigator log": "정규 조사원 기록",
    "polychrome": "폴리크롬",
    "senior investigator log": "선임 조사원 기록",
    "w-engine energy module": "W-엔진 에너지 모듈",
    "w-engine power supply": "변조 W-엔진 전원",
    # 명조
    "advanced enclosure tank": "고급 습유물 밀봉 상자",
    "advanced energy core": "고급 에너지 코어",
    "advanced resonance potion": "고급 공명 촉진제",
    "advanced revival inhaler": "고급 흡입식 소생제",
    "advanced sealed tube": "고급 비밀음파 통",
    "astrite": "별의 소리",
    "forgery premium supply": "응소 특급 물자 상자",
    "medium energy bag": "중급 에너지 주머니",
    "medium energy core": "중급 에너지 코어",
    "medium nutrient block": "중급 영양제",
    "medium resonance potion": "중급 공명 촉진제",
    "medium revival inhaler": "중급 흡입식 소생제",
    "premium enclosure tank": "특급 습유물 밀봉 상자",
    "premium resonance potion": "특급 공명 촉진제",
    "premium tuner": "특급 튜너",
    "shell credit": "클램 코인",
    "weekly challenge supply pack": "군가의 중주 물자 상자",
}

def parse_codes(s):
    # 공백/쉼표로 나누고 대문자로 변환, 입력 순서를 유지하며 중복 제거
    if not s:
        return []
    return list(dict.fromkeys(c.upper() for c in re.split(r"[\s,]+", s) if c))

NUM_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}

def to_korean(name):
    # 아이템 이름을 한국어로. 복수형(primogems, supplies)도 찾아보고, 없으면 원래 이름 유지
    key = name.lower().replace("’", "'").strip()
    for k in (key, key[:-1] if key.endswith("s") else "", key[:-3] + "y" if key.endswith("ies") else ""):
        if k in ITEM_KO:
            return ITEM_KO[k]
    return name.strip()

def to_number(s):
    # "20k" → 20000, "2,222" → 2222, "five" → 5
    s = s.lower().replace(",", "")
    if s in NUM_WORDS:
        return NUM_WORDS[s]
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(k?)", s)
    if not m:
        return None
    return int(float(m.group(1)) * (1000 if m.group(2) else 1))

def format_rewards(s):
    # "Primogem*60;Mora*20000" 또는 "60 primogems and five hero's wit" → "원석×60, 영웅의 경험×5"
    s = (s or "").strip()
    items = []
    if "*" in s:
        for part in s.split(";"):
            name, _, num = part.partition("*")
            items.append((name, to_number(num.strip())))
    else:
        for part in re.split(r",\s*(?:and\s+)?|\s+and\s+", s):
            m = re.fullmatch(r"\s*(\S+)\s+(.+?)\s*", part)
            num = to_number(m.group(1)) if m else None
            items.append((m.group(2), num) if num is not None else (part, None))
    text = ", ".join(to_korean(n) + (f"×{q:,}" if q is not None else "") for n, q in items if n.strip())
    text = re.sub(r"[^\w\s,.'’×+\-「」():]", "", text.replace("_", " "))  # 링크·마크다운·멘션에 쓰이는 문자 제거
    return re.sub(r"\s+", " ", text).strip()[:150]

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
                found[code] = found.get(code) or format_rewards(str(rewards))
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
