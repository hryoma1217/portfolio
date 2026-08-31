"""ポートフォリオの参照切れと未使用ファイルを調べる。

画像のパスを手で書いた以上、必ずどこかで綴りを間違える。
HTMLが指しているファイルが実在するか、逆に誰も参照していない
ファイルが残っていないかを、公開前に機械で確かめる。

0 = 問題なし / 1 = 参照切れあり
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

pages = sorted(ROOT.rglob("*.html"))
pages = [p for p in pages if ".git" not in p.parts]

referenced: set[Path] = set()
missing: list[str] = []

for page in pages:
    text = page.read_text(encoding="utf-8", errors="replace")
    # poster も参照。<video poster="..."> を数えないと、実際は使っている画像が
    # 「どこからも参照されていない」に出てしまい、消す判断を誘う。
    for m in re.finditer(r'(?:src|href|poster)="([^"#?]+)"', text):
        target = m.group(1)
        if target.startswith(("http://", "https://", "mailto:", "data:", "//")):
            continue
        resolved = (page.parent / target).resolve()
        if resolved.exists():
            referenced.add(resolved)
        else:
            missing.append(f"{page.relative_to(ROOT)} -> {target}")

assets = [p for p in (ROOT / "assets").glob("*") if p.is_file()]
unused = [p for p in assets if p.resolve() not in referenced]

print(f"走査したページ: {len(pages)}")
print(f"参照が解決したファイル: {len(referenced)}")

if missing:
    print(f"\n参照切れ {len(missing)}件:")
    for m in missing:
        print(f"  {m}")
else:
    print("参照切れ: なし")

if unused:
    total = sum(p.stat().st_size for p in unused)
    print(f"\nどこからも参照されていない assets {len(unused)}件 ({total//1024}KB):")
    for p in unused:
        print(f"  {p.name}  {p.stat().st_size//1024}KB")
else:
    print("未参照の assets: なし")

raise SystemExit(1 if missing else 0)
