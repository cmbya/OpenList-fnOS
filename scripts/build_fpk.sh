#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$ROOT/package-template"
DIST="$ROOT/dist"
BUILD="$ROOT/.build"

TAG="${1:-}"
if [ -z "$TAG" ]; then
  echo "用法: $0 v4.2.5" >&2
  exit 2
fi
case "$TAG" in
  v*) ;;
  *) TAG="v$TAG" ;;
esac
VERSION="${TAG#v}"

rm -rf "$BUILD" "$DIST"
mkdir -p "$BUILD/pkg" "$BUILD/verify" "$DIST"
cp -a "$TEMPLATE"/. "$BUILD/pkg/"

# 动态写入上游版本。
python3 - "$BUILD/pkg/manifest" "$VERSION" <<'PY'
from pathlib import Path
import re, sys
p=Path(sys.argv[1]); version=sys.argv[2]
s=p.read_text(encoding='utf-8')
s=re.sub(r'^version=.*$', f'version={version}', s, flags=re.M)
s=re.sub(r'^changelog=.*$', f'changelog=自动封装 OpenList v{version}；fnOS x86 原生版，不使用 Docker；升级保留 data。', s, flags=re.M)
s=re.sub(r'^checksum=.*$', 'checksum=PLACEHOLDER', s, flags=re.M)
p.write_text(s, encoding='utf-8')
PY

# app/ 单独压成 app.tgz。
tar -czf "$BUILD/pkg/app.tgz" -C "$BUILD/pkg/app" .
rm -rf "$BUILD/pkg/app"

MD5="$(md5sum "$BUILD/pkg/app.tgz" | awk '{print $1}')"
python3 - "$BUILD/pkg/manifest" "$MD5" <<'PY'
from pathlib import Path
import re, sys
p=Path(sys.argv[1]); md5=sys.argv[2]
s=p.read_text(encoding='utf-8')
s=re.sub(r'^checksum=.*$', f'checksum={md5}', s, flags=re.M)
p.write_text(s, encoding='utf-8')
PY

OUT="$DIST/OpenList_${VERSION}_fnOS_x86.fpk"
(
  cd "$BUILD/pkg"
  tar -czf "$OUT" manifest ICON.PNG ICON_256.PNG LICENSE app.tgz config cmd wizard
)

# 静态校验 FPK 根目录、manifest/app checksum 与关键字段。
tar -xzf "$OUT" -C "$BUILD/verify"
[ -f "$BUILD/verify/manifest" ]
[ -f "$BUILD/verify/app.tgz" ]
[ -d "$BUILD/verify/config" ]
[ -d "$BUILD/verify/cmd" ]
[ -d "$BUILD/verify/wizard" ]

grep -qx 'appname=openlistnative' "$BUILD/verify/manifest"
grep -qx 'platform=x86' "$BUILD/verify/manifest"
grep -qx "version=${VERSION}" "$BUILD/verify/manifest"
grep -qx 'desktop_applaunchname=openlistnative.main' "$BUILD/verify/manifest"
EXPECTED="$(sed -n 's/^checksum=//p' "$BUILD/verify/manifest")"
ACTUAL="$(md5sum "$BUILD/verify/app.tgz" | awk '{print $1}')"
[ "$EXPECTED" = "$ACTUAL" ] || { echo "app.tgz checksum 不一致" >&2; exit 1; }

tar -tzf "$BUILD/verify/app.tgz" | grep -qE '^\./native/bootstrap\.py$|^native/bootstrap\.py$'

# 脚本语法检查。
for f in "$TEMPLATE"/cmd/*; do
  [ -f "$f" ] && bash -n "$f"
done
python3 -m py_compile "$TEMPLATE/app/native/bootstrap.py"

sha256sum "$OUT" | tee "$DIST/SHA256SUMS.txt"
echo "构建成功: $OUT"
