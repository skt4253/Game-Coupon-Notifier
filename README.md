# 🎁 호요버스 쿠폰 교환 링크

원신, 붕괴 스타레일, 젠레스 존 제로 쿠폰 코드를 입력하면 코드가 미리 채워진 교환 링크를 GitHub Actions로 만들어 디스코드에 보내 주는 스크립트입니다.

### "쿠폰 코드 하나하나 복사해서 붙여넣기 귀찮은 사람들을 위한 스크립트"

## ✅ 지원 게임

| 게임 | 교환 페이지 |
|------|-------------|
| 원신 (Genshin Impact) | `https://genshin.hoyoverse.com/ko/gift?code={코드}` |
| 붕괴: 스타레일 (Honkai: Star Rail) | `https://hsr.hoyoverse.com/gift?code={코드}` |
| 젠레스 존 제로 (Zenless Zone Zero) | `https://zenless.hoyoverse.com/redemption?code={코드}` |

링크를 누르면 코드가 채워진 교환 페이지가 열립니다. 로그인하고 서버를 고른 뒤 **교환**만 누르면 됩니다.

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
```

파일명 입력란에 `.github/workflows/coupon.yml` 입력 후 아래 코드 붙여넣기:

```yaml
name: Hoyo Coupon Link

on:
  workflow_dispatch:
    inputs:
      genshin:
        description: '원신 코드 (공백/쉼표 구분)'
        required: false
      hsr:
        description: '붕괴 스타레일 코드 (공백/쉼표 구분)'
        required: false
      zzz:
        description: '젠레스 존 제로 코드 (공백/쉼표 구분)'
        required: false

jobs:
  coupon:
    runs-on: ubuntu-latest
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
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
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

### Step 5. 실행

repo → **Actions** → **Hoyo Coupon Link** → **Run workflow**

게임별 입력칸에 코드를 공백이나 쉼표로 구분해 넣고 **Run workflow**를 누릅니다. 하지 않는 게임은 비워 두면 됩니다.

```
원신:           ABC123 DEF456
붕괴 스타레일:   STARRAIL
젠레스 존 제로:  ZZZ2026
```

> 💡 GitHub 모바일 앱에서도 **Actions** 탭에서 바로 실행할 수 있습니다.

## 📱 알림 예시

**🎁 쿠폰 교환 링크**

- **원신**: [ABC123](https://genshin.hoyoverse.com/ko/gift?code=ABC123), [DEF456](https://genshin.hoyoverse.com/ko/gift?code=DEF456)
- **붕괴 스타레일**: [STARRAIL](https://hsr.hoyoverse.com/gift?code=STARRAIL)
- **젠레스 존 제로**: [ZZZ2026](https://zenless.hoyoverse.com/redemption?code=ZZZ2026)

버튼: `원신 ABC123` `원신 DEF456` `스레 STARRAIL` `젠존제 ZZZ2026`

- 코드는 대문자로 바뀌고, 중복은 입력 순서를 유지한 채 제거됩니다.
- 버튼은 최대 25개까지 붙습니다. 넘치는 코드는 임베드 링크로만 제공됩니다.

## 🔧 문제 해결

| 증상 | 원인 및 조치 |
|------|--------------|
| `코드를 하나 이상 입력해 주세요.` 로 실패 | 입력칸이 모두 비어 있음 |
| `HTTP 401` / `HTTP 404` | 웹훅 URL이 틀렸거나 삭제됨. 새로 만들어 Secret 갱신 |
| 임베드는 오는데 버튼이 없음 | 디스코드 웹훅 버튼 지원 문제. Actions 로그의 응답 확인 |
| 알림이 아예 안 옴 | Actions 로그에서 secret 누락 여부 확인 |

## ⚠️ 주의사항

- 호요버스 교환 페이지는 URL 하나에 코드 하나만 받으므로 코드마다 링크가 하나씩 생성됩니다
- 디스코드는 버튼 하나로 여러 탭을 여는 기능을 지원하지 않습니다
- **Secrets에 저장된 값은 절대 외부에 공유하지 마세요**
