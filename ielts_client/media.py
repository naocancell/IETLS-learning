# -*- coding: utf-8 -*-
"""
听力音频的发现与准备。

仓库/本地只需要把官方音频（zip 压缩包或散装 mp3）放进 `听力/` 目录，
程序会按文件名自动识别「第几本 / 第几套 / 第几段」，并在第一次播放时
把对应文件解压（复制）到 `ielts_client/media/cXX/tY/sZ.mp3`。

识别不了的命名，可以在 `听力/audio_map.json` 里手动指定，例如：
{
  "c05/t1/s1.mp3": "Cambridge 5/CD1/Track 02.mp3",
  "c05/t1/s2.mp3": "Cambridge-IELTS-05.zip::CD1/Track 03.mp3"
}
左边是题库 JSON 中 part.audio 的值，右边是相对 `听力/` 的路径；
zip 内文件用 `压缩包名::包内路径` 表示。
"""
import json
import os
import re
import shutil
import threading
import zipfile

AUDIO_EXT = ('.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac')

_BOOK_PATTERNS = [
    re.compile(r'(?i)(?:IELTS|Cambridge|剑桥雅思|剑雅|剑)[^0-9]{0,24}?0*(\d{1,2})(?!\d)'),
    re.compile(r'(?i)(?<![a-z])C0*(\d{1,2})[ _\-]?T\d'),
]
_TEST_PATTERNS = [
    re.compile(r'(?i)(?:Test|Tests)[ _\-]*0*(\d)(?!\d)'),
    re.compile(r'(?i)(?<![a-z])T0*(\d)[ _\-]?(?:S|P)\d'),
    re.compile(r'第\s*(\d)\s*套'),
]
_SECTION_PATTERNS = [
    re.compile(r'(?i)(?:Section|Part|Sec)[ _\-]*0*([1-4])(?!\d)'),
    re.compile(r'(?i)(?<![a-z])T\d[ _\-]?(?:S|P)0*([1-4])(?!\d)'),
    re.compile(r'第\s*([1-4])\s*(?:部分|节|段)'),
]


def _first(patterns, text):
    for p in patterns:
        m = p.findall(text)
        if m:
            return int(m[-1])
    return None


def parse_name(container, member=''):
    """从 (压缩包名, 包内路径) 或 (文件相对路径, '') 推断 (book, test, section)。"""
    full = (container + '/' + member) if member else container
    base = os.path.basename(full)
    # 先看文件名本身，再看完整路径（目录 / 压缩包名）
    book = _first(_BOOK_PATTERNS, base) or _first(_BOOK_PATTERNS, full)
    test = _first(_TEST_PATTERNS, base) or _first(_TEST_PATTERNS, full)
    sec = _first(_SECTION_PATTERNS, base)
    if sec is None:
        sec = _first(_SECTION_PATTERNS, full)
    if book is not None and not (1 <= book <= 30):
        book = None
    return book, test, sec


def key_for(book, test, sec, ext='.mp3'):
    return 'c%02d/t%d/s%d%s' % (book, test, sec, ext)


class MediaLibrary:
    """扫描音频来源目录，按需把文件准备到 media 目录。"""

    def __init__(self, src_dirs, media_dir):
        self.src_dirs = [d for d in src_dirs if d]
        self.media_dir = media_dir
        self.index = {}        # 'c04/t1/s1.mp3' -> (container_abs, member or None)
        self.unmapped = []     # 识别失败的音频文件
        self.duplicates = []   # 同一个 key 找到多个来源
        self._lock = threading.Lock()
        self._file_locks = {}
        self.scan()

    # ---------- 扫描 ----------
    def scan(self):
        self.index, self.unmapped, self.duplicates = {}, [], []
        for src in self.src_dirs:
            if not os.path.isdir(src):
                continue
            for root, _dirs, files in os.walk(src):
                for fn in sorted(files):
                    path = os.path.join(root, fn)
                    rel = os.path.relpath(path, src).replace('\\', '/')
                    low = fn.lower()
                    if low.endswith('.zip'):
                        self._scan_zip(path, rel)
                    elif low.endswith(AUDIO_EXT):
                        self._add(parse_name(rel), (path, None), rel)
            self._apply_map(src)

    def _scan_zip(self, path, rel):
        try:
            with zipfile.ZipFile(path) as z:
                for info in z.infolist():
                    if info.is_dir():
                        continue
                    name = _zip_name(info)
                    if not name.lower().endswith(AUDIO_EXT):
                        continue
                    self._add(parse_name(rel, name), (path, info.filename), rel + '::' + name)
        except zipfile.BadZipFile:
            self.unmapped.append(rel + '（压缩包损坏，无法读取）')

    def _add(self, parsed, source, label):
        book, test, sec = parsed
        if None in (book, test, sec):
            self.unmapped.append(label)
            return
        ext = os.path.splitext(label)[1].lower() or '.mp3'
        key = key_for(book, test, sec, '.mp3' if ext == '.mp3' else ext)
        if key in self.index:
            self.duplicates.append((key, label))
            return
        self.index[key] = source

    def _apply_map(self, src):
        mp = os.path.join(src, 'audio_map.json')
        if not os.path.isfile(mp):
            return
        with open(mp, encoding='utf-8-sig') as f:
            mapping = json.load(f)
        for key, target in mapping.items():
            if key.startswith('_'):
                continue
            if '::' in target:
                zrel, member = target.split('::', 1)
                zpath = os.path.join(src, zrel)
                real = None
                try:
                    with zipfile.ZipFile(zpath) as z:
                        for info in z.infolist():
                            if _zip_name(info) == member or info.filename == member:
                                real = info.filename
                                break
                except (OSError, zipfile.BadZipFile):
                    pass
                if real:
                    self.index[key] = (zpath, real)
                else:
                    self.unmapped.append('audio_map.json: %s -> %s（找不到）' % (key, target))
            else:
                path = os.path.join(src, target)
                if os.path.isfile(path):
                    self.index[key] = (path, None)
                else:
                    self.unmapped.append('audio_map.json: %s -> %s（找不到）' % (key, target))

    # ---------- 查询 / 准备 ----------
    def local_path(self, key):
        key = key.replace('\\', '/').lstrip('/')
        if '..' in key.split('/'):
            return None
        return os.path.join(self.media_dir, *key.split('/'))

    def available(self, key):
        p = self.local_path(key)
        return bool(p) and (os.path.isfile(p) or key in self.index)

    def ensure(self, key):
        """返回可直接读取的本地文件路径；需要时从来源复制/解压。找不到返回 None。"""
        dst = self.local_path(key)
        if not dst:
            return None
        if os.path.isfile(dst):
            return dst
        src = self.index.get(key)
        if not src:
            return None
        with self._lock:
            lock = self._file_locks.setdefault(key, threading.Lock())
        with lock:
            if os.path.isfile(dst):
                return dst
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            tmp = dst + '.part'
            container, member = src
            if member is None:
                shutil.copyfile(container, tmp)
            else:
                with zipfile.ZipFile(container) as z, z.open(member) as fi, open(tmp, 'wb') as fo:
                    shutil.copyfileobj(fi, fo, 1024 * 1024)
            os.replace(tmp, dst)
        return dst

    def prepare_all(self, keys=None, log=print):
        done = 0
        for key in sorted(keys or self.index):
            if self.local_path(key) and os.path.isfile(self.local_path(key)):
                continue
            if self.ensure(key):
                done += 1
                log('  已准备 ' + key)
        return done


def _zip_name(info):
    """zip 里的中文文件名经常是 GBK 编码却没打 UTF-8 标记，这里尽量还原。"""
    name = info.filename
    if info.flag_bits & 0x800:
        return name
    try:
        raw = name.encode('cp437')
    except UnicodeEncodeError:
        return name
    for enc in ('utf-8', 'gbk'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return name
