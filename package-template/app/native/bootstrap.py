#!/usr/bin/env python3
import argparse
import hashlib
import os
import shutil
import stat
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

REPO = "OpenListTeam/OpenList"
ASSET = "openlist-linux-amd64.tar.gz"


def log(msg: str):
    print(f"[OpenList fnOS] {msg}", flush=True)


def download(url: str, dst: Path):
    req = urllib.request.Request(url, headers={"User-Agent": "OpenList-fnOS-native/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r, open(dst, "wb") as f:
        log(f"下载 {url}")
        shutil.copyfileobj(r, f, length=1024 * 1024)


def parse_expected_md5(text: str):
    for raw in text.splitlines():
        line = raw.strip()
        if not line or ASSET not in line:
            continue
        parts = line.replace("*", " ").split()
        for p in parts:
            if len(p) == 32 and all(c in "0123456789abcdefABCDEF" for c in p):
                return p.lower()
    return None


def md5sum(path: Path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_extract_binary(archive: Path, dst: Path):
    with tarfile.open(archive, "r:gz") as tf:
        members = [m for m in tf.getmembers() if m.isfile() and Path(m.name).name == "openlist"]
        if not members:
            raise RuntimeError("官方压缩包中没有找到 openlist 可执行文件")
        m = members[0]
        src = tf.extractfile(m)
        if src is None:
            raise RuntimeError("无法读取 openlist 可执行文件")
        with open(dst, "wb") as out:
            shutil.copyfileobj(src, out)


def ensure_data_link(runtime: Path, data: Path):
    data.mkdir(parents=True, exist_ok=True)
    link = runtime / "data"
    if link.is_symlink():
        try:
            current = Path(os.readlink(link))
        except OSError:
            current = None
        if current != data:
            link.unlink()
            link.symlink_to(data, target_is_directory=True)
    elif link.exists():
        if link.is_dir() and not any(link.iterdir()):
            link.rmdir()
            link.symlink_to(data, target_is_directory=True)
        elif link.resolve() != data.resolve():
            raise RuntimeError(f"{link} 已存在且不是可替换的空目录/软链接")
    else:
        link.symlink_to(data, target_is_directory=True)


def install(runtime: Path, data: Path, version: str):
    runtime.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)
    binary = runtime / "openlist"
    marker = runtime / "VERSION"

    if binary.is_file() and marker.is_file() and marker.read_text(encoding="utf-8").strip() == version:
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        ensure_data_link(runtime, data)
        log(f"OpenList {version} 已存在，跳过重新下载")
        return

    tag = f"v{version}"
    base = f"https://github.com/{REPO}/releases/download/{tag}"
    with tempfile.TemporaryDirectory(prefix="openlist-fnos-") as td_s:
        td = Path(td_s)
        archive = td / ASSET
        download(f"{base}/{ASSET}", archive)

        # 官方 Release 同时提供 md5.txt。校验文件能下载时严格校验；若官方未来取消该文件则继续进行结构校验。
        try:
            md5_file = td / "md5.txt"
            download(f"{base}/md5.txt", md5_file)
            expected = parse_expected_md5(md5_file.read_text(encoding="utf-8", errors="ignore"))
            if expected:
                actual = md5sum(archive)
                if actual != expected:
                    raise RuntimeError(f"OpenList 下载校验失败：期望 {expected}，实际 {actual}")
                log("官方 md5 校验通过")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            log("官方未提供 md5.txt，跳过 MD5 校验")

        extracted = td / "openlist"
        safe_extract_binary(archive, extracted)
        if extracted.stat().st_size < 1024 * 1024:
            raise RuntimeError("解压得到的 openlist 文件异常过小")
        extracted.chmod(0o755)

        newbin = runtime / "openlist.new"
        shutil.copy2(extracted, newbin)
        newbin.chmod(0o755)
        os.replace(newbin, binary)
        marker.write_text(version + "\n", encoding="utf-8")
        log(f"已安装 OpenList {version} Linux amd64")

    ensure_data_link(runtime, data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--version", required=True)
    args = ap.parse_args()
    install(Path(args.runtime), Path(args.data), args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
