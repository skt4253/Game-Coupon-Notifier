# 🎁 게임 쿠폰 알림

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
| [Ennead API](https://api.ennead.cc/mihoyo/genshin/codes) | 비공식 공개 API. **seria가 실패할 때만** 대신 사용 (한 묶음에서 하나만 쓸 수 있는 코드까지 전부 실려 있어 평소엔 쓰지 않음) |
| HoYoLAB 게임 가이드 | 공식. 특별 방송 코드가 공개된 기간에만 채워짐 |
| [명조 Fandom 위키](https://wutheringwaves.fandom.com/wiki/Redemption_Code) | 명조 전용. Active 표에서 만료일이 지난 코드는 제외 |

모두 무료이며 로그인·API 키가 필요 없습니다. 한쪽이 실패해도 나머지로 계속 진행합니다.

## 📋 사전 준비

- GitHub 계정
- 디스코드 계정 (링크를 받을 채널)

---

## 🚀 설치 방법

### Step 1. Repository 생성

1. GitHub에서 **New repository** 클릭
2. Repository name 입력 (예: `game-coupon-notifier`)
3. **Private** 선택
4. **Add a README file** 체크 후 생성

### Step 2. 파일 업로드

repo 메인 페이지 → **Add file** → **Create new file**로 아래 두 파일을 만들고, 이 repo에 있는 같은 파일의 내용을 그대로 붙여넣습니다. 파일명 입력란에 경로까지 입력하면 폴더가 함께 만들어집니다.

| 파일 | 역할 |
|------|------|
| [`coupon.py`](coupon.py) | 코드 수집 후 디스코드로 전송하는 스크립트 |
| [`.github/workflows/coupon.yml`](.github/workflows/coupon.yml) | 1시간마다 스크립트를 실행하는 GitHub Actions 워크플로 |

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

repo → **Actions** → **Game Coupon Notifier** → **Run workflow** → 입력칸을 모두 비운 채 **Run workflow**

첫 실행에서는 현재 유효한 코드가 한꺼번에 전송되고, 이후로는 새 코드만 전송됩니다.

---

## ⏰ 자동 수집

**1시간마다** (매시 15분) 자동 실행됩니다.

- 이미 보낸 코드는 `sent.json`에 기록되어 다시 보내지 않습니다. 이 기록은 repo가 아닌 **Actions 캐시**에 저장되므로 Fork하거나 복사해도 따라가지 않습니다.
- 7일 넘게 실행되지 않으면 캐시가 삭제되어, 다음 실행 때 현재 유효한 코드가 다시 한꺼번에 전송될 수 있습니다.
- 새 코드가 없으면 아무 메시지도 보내지 않습니다.
- 주기를 바꾸려면 `coupon.yml`의 cron 값을 UTC 기준으로 수정하세요. (GitHub Actions 스케줄은 수 분~수십 분 지연될 수 있습니다.)

> 💡 Private repo의 Actions 무료 한도는 월 2,000분입니다. 1시간 주기면 월 약 750분으로 충분합니다. Public repo는 무제한입니다.

## ✍️ 직접 입력

repo → **Actions** → **Game Coupon Notifier** → **Run workflow**에서 게임별 입력칸에 코드를 공백이나 쉼표로 구분해 넣습니다. 하지 않는 게임은 비워 두면 됩니다. **모두 비우면 자동 수집**이 실행됩니다.

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

- **원신**: [VESNAONPATROL](https://genshin.hoyoverse.com/ko/gift?code=VESNAONPATROL) · 원석×40, 모라×20,000, 영웅의 경험×3
- **젠레스 존 제로**: [ZZZINK32](https://zenless.hoyoverse.com/redemption?code=ZZZINK32) · 폴리크롬×20, 데니×2,222
- **명조**: `WUTHERINGGIFT` · 별의 소리×50, 클램 코인×10,000  
  *게임 내 터미널 → 설정 → 기타 설정 → 교환 코드에 입력하세요.*

버튼: `원신 VESNAONPATROL` `젠존제 ZZZINK32`

- 명조는 버튼이 붙지 않습니다.
- 보상 아이템은 게임 데이터(원신·스타레일: yatta.moe, 젠레스: HoYoWiki, 명조: encore.moe)에서 가져온 공식 한국어 이름으로 표시합니다. 목록에 없는 아이템은 영어로 표시됩니다.
- 코드는 대문자로 바뀌고, 중복은 입력 순서를 유지한 채 제거됩니다.
- 버튼은 최대 25개까지 붙습니다. 넘치는 코드는 임베드 링크로만 제공됩니다.

## 🔧 문제 해결

| 증상 | 원인 및 조치 |
|------|--------------|
| `HTTP 401` / `HTTP 404` | 웹훅 URL이 틀렸거나 삭제됨. 새로 만들어 Secret 갱신 |
| `[WARN] ... 수집 실패` | 수집처 일시 장애. 다른 수집처로 계속 진행되며 다음 실행 때 재시도 |
| 임베드는 오는데 버튼이 없음 | 디스코드 웹훅 버튼 지원 문제. Actions 로그의 응답 확인 |
| 같은 코드를 다시 받고 싶음 | 직접 입력으로 실행. 전부 다시 받으려면 **Actions → Caches**에서 `sent-` 캐시 삭제 |
| 자동 실행이 안 됨 | 원래 Public repo는 60일간 활동이 없으면 스케줄이 꺼지지만, 워크플로가 실행마다 스스로 재활성화합니다. 그래도 꺼졌다면 Actions 탭에서 다시 활성화 |

## ⚠️ 주의사항

- 호요버스 교환 페이지는 URL 하나에 코드 하나만 받으므로 코드마다 링크가 하나씩 생성됩니다
- 디스코드는 버튼 하나로 여러 탭을 여는 기능을 지원하지 않습니다
- seria·Ennead API는 개인이 운영하는 비공식 서비스라 언젠가 중단될 수 있습니다. seria가 멈추면 Ennead가 대신하지만, 그때는 같은 묶음의 코드가 여러 개 올 수 있습니다 (하나만 교환됨)
- 명조 코드는 위키 편집자가 갱신하는 만큼 반영되므로 공식 발표보다 늦을 수 있습니다
- 외부에서 수집한 값은 코드 형식(영문 대문자·숫자 4~30자)만 통과시키고, 보상 문구의 링크·마크다운·멘션 문자는 제거한 뒤 사용합니다
- **Secrets에 저장된 값은 절대 외부에 공유하지 마세요**
