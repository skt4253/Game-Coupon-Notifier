"""디스코드 웹훅으로 쿠폰 교환 링크를 보냅니다.

환경변수
  DISCORD_WEBHOOK_URL  웹훅 URL (필수)
  GENSHIN, HSR, ZZZ    게임별 코드들 (공백/쉼표 구분, 선택)
"""

import json
import os
import sys
import urllib.error
import urllib.request

from coupon import COLOR, EMPTY_MESSAGE, TITLE, build, overflow_footer


def main() -> int:
    fields, buttons, overflow = build({
        "genshin": os.environ.get("GENSHIN"),
        "hsr": os.environ.get("HSR"),
        "zzz": os.environ.get("ZZZ"),
    })
    if not fields:
        print(EMPTY_MESSAGE, file=sys.stderr)
        return 1

    embed = {
        "title": TITLE,
        "color": COLOR,
        "fields": [{"name": n, "value": v, "inline": False} for n, v in fields],
    }
    if overflow:
        embed["footer"] = {"text": overflow_footer()}

    # 링크 버튼(style 5)은 한 줄에 5개, 최대 5줄까지 붙일 수 있습니다.
    components = [
        {
            "type": 1,
            "components": [
                {"type": 2, "style": 5, "label": label, "url": url}
                for label, url in buttons[i:i + 5]
            ],
        }
        for i in range(0, len(buttons), 5)
    ]

    # 애플리케이션 소유가 아닌 웹훅은 with_components=true 를 붙여야 버튼이 표시됩니다.
    url = os.environ["DISCORD_WEBHOOK_URL"]
    url += ("&" if "?" in url else "?") + "with_components=true"
    body = json.dumps({"embeds": [embed], "components": components}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "Game-Coupon (webhook, 1.0)"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as res:
            print(f"전송 완료 ({res.status})")
    except urllib.error.HTTPError as e:
        print(f"전송 실패 ({e.code}): {e.read().decode(errors='replace')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
