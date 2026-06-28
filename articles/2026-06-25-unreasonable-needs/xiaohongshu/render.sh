#!/bin/bash
# 小红书图文卡渲染：编辑 gen.mjs 里的 cards 数组 → 跑这个脚本 → png/ 出 1080×1440 成品
set -e
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
rm -rf html png2x png && mkdir -p png2x png
node gen.mjs "$PWD/html"
for f in html/*.html; do
  base=$(basename "$f" .html)
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-color-profile=srgb \
    --window-size=1080,1440 --force-device-scale-factor=2 \
    --screenshot="png2x/$base.png" "file://$PWD/$f" >/dev/null 2>&1
  sips -z 1440 1080 "png2x/$base.png" --out "png/$base.png" >/dev/null 2>&1
done
echo "✅ png/ 已生成 $(ls png/ | wc -l | tr -d ' ') 张 1080×1440 卡片"
