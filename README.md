# 🎁 호요버스 쿠폰 교환 링크

원신, 붕괴 스타레일, 젠레스 존 제로, 명조의 **새 쿠폰 코드를 자동으로 수집**해서, 코드가 미리 채워진 교환 링크를 GitHub Actions로 디스코드에 보내 주는 스크립트입니다. 직접 코드를 넣어 링크를 만들 수도 있습니다.

### "쿠폰 코드 찾아다니고 하나하나 복사해서 붙여넣기 귀찮은 사람들을 위한 스크립트"

## ✅ 지원 게임

| 게임 | 교환 페이지 |
|------|-------------|
| 원신 (Genshin Impact) | `https://genshin.hoyoverse.com/ko/gift?code={코드}` |
| 붕괴: 스타레일 (Honkai: Star Rail) | `https://hsr.hoyoverse.com/gift?code={코드}` |
| 젠레스 존 제로 (Zenless Zone Zero) | `https://zenless.hoyoverse.com/redemption?code={코드}` |
| 명조: 워더링 웨이브 (Wuthering Waves) | 웹 교환 페이지 없음 → 코드만 전송 |

링크를 누르면 코드가 채워진 교환 페이지가 열립니다. 로그인하고 서버를 고른 뒤 **교환**만 누르면 됩니다.

명조는 게임 안에서만 교환할 수 있어 링크·버튼 없이 코드와 입력 위치(터미널 → 설정 → 기타 설정 → 교환 코드)만 보내 드립니다.

## 🔎 코드 수집처

| 수집처 | 설명 |
|--------|------|
| [hoyo-codes.seria.moe](https://hoyo-codes.seria.moe/codes?game=genshin) | 비공식 공개 API. 유효한(`OK`) 코드와 보상 정보 |
| HoYoLAB 게임 가이드 | 공식. 특별 방송 코드가 공개된 기간에만 채워짐 |
| [명조 Fandom 위키](https://wutheringwaves.fandom.com/wiki/Redemption_Code) | 명조 전용. Active 표에서 만료일이 지난 코드는 제외 |

둘 다 무료이며 로그인·API 키가 필요 없습니다. 한쪽이 실패해도 나머지로 계속 진행합니다.

## 📋 사전 준비

- GitHub 계정
- 디스코드 계정 (링크를 받을 채널)

---

## 🚀 설치 방법

### Step 1. Repository 생성

1. GitHub에서 **New repository** 클릭
2. Repository name 입력 (예: `hoyo-coupon-link`)
3. **Private** 선택
4. **Add a README file** 체크 후 생성

### Step 2. 파일 업로드

repo 메인 페이지 → **Add file** → **Create new file**

**`coupon.py`** 생성 후 아래 코드 붙여넣기:

```python
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
```

파일명 입력란에 `.github/workflows/coupon.yml` 입력 후 아래 코드 붙여넣기:

```yaml
name: Hoyo Coupon Link

on:
  schedule:
    - cron: '7 */2 * * *'  # 2시간마다 새 코드 자동 수집 (UTC 기준, 매 짝수 시 7분)
  workflow_dispatch:
    inputs:
      genshin:
        description: '원신 코드 (공백/쉼표 구분, 모두 비우면 자동 수집)'
        required: false
      hsr:
        description: '붕괴 스타레일 코드 (공백/쉼표 구분)'
        required: false
      zzz:
        description: '젠레스 존 제로 코드 (공백/쉼표 구분)'
        required: false
      wuwa:
        description: '명조 코드 (공백/쉼표 구분, 링크 없이 코드만 전송)'
        required: false

permissions:
  contents: write  # sent.json 커밋용

concurrency:
  group: coupon
  cancel-in-progress: false

jobs:
  coupon:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: '3.11'
      - run: pip install requests
      - run: python coupon.py
        env:
          GENSHIN: ${{ inputs.genshin }}
          HSR: ${{ inputs.hsr }}
          ZZZ: ${{ inputs.zzz }}
          WUWA: ${{ inputs.wuwa }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      - name: 보낸 코드 기록 커밋
        run: |
          git add sent.json 2>/dev/null || true
          if git diff --cached --quiet; then exit 0; fi
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git commit -m "보낸 쿠폰 코드 기록 갱신"
          git push
```

---

### Step 3. 디스코드 웹훅

1. 링크 받을 디스코드 채널 → **⚙️ 채널 편집** → **연동** → **웹후크 만들기**
2. 생성된 웹훅 클릭 → 이름 지정(선택) → **웹후크 URL 복사** → **변경사항 저장**

> ⚠️ 웹훅 URL만 있으면 누구나 해당 채널에 메시지를 보낼 수 있으니 Secret에만 저장하세요. 유출 시 웹훅을 삭제하고 새로 만들면 됩니다.

---

### Step 4. Secrets 등록

repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret 이름 | 값 |
|------------|-----|
| `DISCORD_WEBHOOK_URL` | 디스코드 웹훅 URL |

> ⚠️ 값을 붙여넣을 때 앞뒤 따옴표·공백·줄바꿈이 섞이지 않게 한 줄로만 입력하세요.

---

### Step 5. 테스트 실행

repo → **Actions** → **Hoyo Coupon Link** → **Run workflow** → 입력칸을 모두 비운 채 **Run workflow**

첫 실행에서는 현재 유효한 코드가 한꺼번에 전송되고, 이후로는 새 코드만 전송됩니다.

---

## ⏰ 자동 수집

**2시간마다** (UTC 짝수 시 7분 = KST 홀수 시 7분) 자동 실행됩니다.

- 이미 보낸 코드는 repo의 `sent.json`에 기록되어 다시 보내지 않습니다. (워크플로가 자동 커밋)
- 새 코드가 없으면 아무 메시지도 보내지 않습니다.
- 주기를 바꾸려면 `coupon.yml`의 cron 값을 UTC 기준으로 수정하세요. (GitHub Actions 스케줄은 수 분~수십 분 지연될 수 있습니다.)

> 💡 Private repo의 Actions 무료 한도는 월 2,000분입니다. 2시간 주기면 월 약 360분으로 충분합니다. Public repo는 무제한입니다.

## ✍️ 직접 입력

repo → **Actions** → **Hoyo Coupon Link** → **Run workflow**에서 게임별 입력칸에 코드를 공백이나 쉼표로 구분해 넣습니다. 하지 않는 게임은 비워 두면 됩니다. **모두 비우면 자동 수집**이 실행됩니다.

```
원신:           ABC123 DEF456
붕괴 스타레일:   STARRAIL
젠레스 존 제로:  ZZZ2026
명조:           WUTHERINGGIFT
```

터미널(gh CLI)에서:

```bash
gh workflow run coupon.yml -f genshin="ABC123 DEF456" -f hsr="STARRAIL" -f wuwa="WUTHERINGGIFT"
```

> 💡 GitHub 모바일 앱에서도 **Actions** 탭에서 바로 실행할 수 있습니다.

## 📱 알림 예시

**🎁 새 쿠폰 교환 링크**

- **원신**: [VESNAONPATROL](https://genshin.hoyoverse.com/ko/gift?code=VESNAONPATROL) · Primogem×40, Mora×20000, Hero's Wit×3
- **젠레스 존 제로**: [ZZZINK32](https://zenless.hoyoverse.com/redemption?code=ZZZINK32) · Polychrome×20, Denny×2,222
- **명조**: `WUTHERINGGIFT` · Astrite×50, Shell Credit×10000  
  *게임 내 터미널 → 설정 → 기타 설정 → 교환 코드에 입력하세요.*

버튼: `원신 VESNAONPATROL` `젠존제 ZZZINK32`

- 명조는 버튼이 붙지 않습니다.
- 코드는 대문자로 바뀌고, 중복은 입력 순서를 유지한 채 제거됩니다.
- 버튼은 최대 25개까지 붙습니다. 넘치는 코드는 임베드 링크로만 제공됩니다.

## 🔧 문제 해결

| 증상 | 원인 및 조치 |
|------|--------------|
| `HTTP 401` / `HTTP 404` | 웹훅 URL이 틀렸거나 삭제됨. 새로 만들어 Secret 갱신 |
| `[WARN] ... 수집 실패` | 수집처 일시 장애. 다른 수집처로 계속 진행되며 다음 실행 때 재시도 |
| 임베드는 오는데 버튼이 없음 | 디스코드 웹훅 버튼 지원 문제. Actions 로그의 응답 확인 |
| 같은 코드를 다시 받고 싶음 | `sent.json`에서 해당 코드를 지우거나 직접 입력으로 실행 |
| 자동 실행이 안 됨 | Public repo는 60일간 활동이 없으면 스케줄이 꺼짐. Actions 탭에서 다시 활성화 |

## ⚠️ 주의사항

- 호요버스 교환 페이지는 URL 하나에 코드 하나만 받으므로 코드마다 링크가 하나씩 생성됩니다
- 디스코드는 버튼 하나로 여러 탭을 여는 기능을 지원하지 않습니다
- seria API는 개인이 운영하는 비공식 서비스라 언젠가 중단될 수 있습니다
- 명조 코드는 위키 편집자가 갱신하는 만큼 반영되므로 공식 발표보다 늦을 수 있습니다
- 외부에서 수집한 값은 코드 형식(영문 대문자·숫자 4~30자)만 통과시키고, 보상 문구의 링크·마크다운·멘션 문자는 제거한 뒤 사용합니다
- **Secrets에 저장된 값은 절대 외부에 공유하지 마세요**
