# Game-Coupon

원신, 붕괴: 스타레일, 젠레스 존 제로 쿠폰 코드로 코드가 미리 채워진 교환 링크를 만들어 디스코드에 보냅니다.

## GitHub Actions + 웹훅

1. 저장소 **Settings → Secrets and variables → Actions**에 `DISCORD_WEBHOOK_URL`을 추가합니다.
2. **Actions → 쿠폰 링크 보내기 → Run workflow**를 누르고 게임별 코드를 공백이나 쉼표로 구분해 입력합니다.

로컬에서 보낼 때:

```powershell
$env:DISCORD_WEBHOOK_URL = "웹훅 URL"
$env:GENSHIN = "ABC123 DEF456"
python webhook.py
```

## 슬래시 명령어 봇 (선택)

`/쿠폰 원신:ABC123 DEF456 스타레일:STARRAIL 젠레스:ZZZ2026`

```powershell
pip install -r requirements.txt
$env:DISCORD_TOKEN = "봇 토큰"
python bot.py
```

봇 초대 URL에는 `bot`, `applications.commands` 스코프가 필요합니다. 봇은 계속 실행해 둘 서버가 있어야 합니다.
