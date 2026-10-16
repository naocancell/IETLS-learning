# -*- coding: utf-8 -*-
"""
题库校验：python tools/validate_data.py [c05/t1 ...] [--strict]

检查每套题 listening.json / reading.json：
  * 题号 1–40 连续且不重复，每题都有答案
  * 选择 / 判断 / 配对题的答案在选项里；判断题只能是 TRUE/FALSE/NOT GIVEN 或 YES/NO/NOT GIVEN
  * 多选题 answer_set 数量 = 小题数，且都在选项里
  * 填空题的 {{n}} 空位与题目一一对应；blanks 数量与答案组数一致
  * 字数限制：标准答案本身不能超过 limit（常见录入错误）
  * 阅读 evidence 必须能在原文中原样找到
  * 图片存在；听力音频能在 听力/ 或 media/ 中找到（缺失仅警告）
退出码：有错误时为 1。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'ielts_client'))

TFNG = {'TRUE', 'FALSE', 'NOT GIVEN'}
YNNG = {'YES', 'NO', 'NOT GIVEN'}
CHOICE = {'single_choice', 'tfng', 'ynng', 'matching', 'multi_choice'}
TYPES = CHOICE | {'completion'}
PH = re.compile(r'\{\{(\d+)(?:\.(\d+))?\}\}')
NUM = re.compile(r'^[\d.,:/%£$€]+(?:st|nd|rd|th|am|pm|km|kg|m)?$', re.I)


def strip_opt(s):
    """'(the) Tower of London' -> 'the Tower of London'（取最长形式算字数）"""
    return re.sub(r'[()]', '', s)


def count_words(s, number_free):
    words = [w for w in re.split(r'[\s\-–]+', strip_opt(s).strip()) if w]
    if number_free:
        words = [w for w in words if not NUM.match(w)]
    return len(words)


class Report:
    def __init__(self, name):
        self.name, self.errors, self.warnings = name, [], []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def text_of(part):
    return '\n'.join(filter(None, [part.get('passage_title'), part.get('intro'), part.get('passage')]))


def validate(path, media=None):
    rep = Report(os.path.relpath(path, ROOT))
    try:
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
    except ValueError as e:
        rep.err('JSON 格式错误：%s' % e)
        return rep
    base = os.path.dirname(path)
    module = d.get('module')
    if module not in ('listening', 'reading'):
        rep.err('module 必须是 listening 或 reading')
    if d.get('schema_version') != 2:
        rep.warn('schema_version 不是 2')
    for k in ('book', 'test', 'title', 'parts'):
        if k not in d:
            rep.err('缺少字段 %s' % k)
    if module == 'reading' and d.get('variant') not in ('academic', 'general'):
        rep.err('阅读需要 variant: academic / general')
    parts = d.get('parts', [])
    expect_parts = 4 if module == 'listening' else (3 if d.get('variant') == 'academic' else None)
    if expect_parts and len(parts) != expect_parts:
        rep.warn('parts 数量为 %d（通常是 %d）' % (len(parts), expect_parts))
    ids = []
    for pi, part in enumerate(parts, 1):
        where = 'Part %s' % part.get('number', pi)
        passage = text_of(part)
        if module == 'listening':
            if not part.get('audio'):
                rep.err('%s 缺少 audio' % where)
            elif media and not media.available(part['audio']):
                rep.warn('%s 音频 %s 暂未找到（听力/ 目录里没有可识别的文件）' % (where, part['audio']))
            if part.get('transcript') and not os.path.isfile(os.path.join(base, part['transcript'])):
                rep.warn('%s transcript 文件不存在：%s（运行 tools/transcribe.py 生成）' % (where, part['transcript']))
        else:
            if not part.get('passage'):
                rep.err('%s 缺少 passage' % where)
        for img in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', passage):
            if not os.path.isfile(os.path.join(base, img)):
                rep.err('%s 原文图片不存在：%s' % (where, img))
        qr = part.get('questions_range')
        for g in part.get('groups', []):
            a, b = g.get('range', [None, None])
            gw = '%s Q%s–%s' % (where, a, b)
            t = g.get('type')
            if t not in TYPES:
                rep.err('%s 未知题型 %r' % (gw, t))
                continue
            if not g.get('category'):
                rep.warn('%s 缺少 category（成绩单按题型统计会归到“其他”）' % gw)
            if not g.get('instruction'):
                rep.warn('%s 缺少 instruction' % gw)
            if g.get('image') and not os.path.isfile(os.path.join(base, g['image'])):
                rep.err('%s 图片不存在：%s' % (gw, g['image']))
            qs = g.get('questions', [])
            qids = [q.get('id') for q in qs]
            if qids != list(range(a, b + 1)):
                rep.err('%s 题号 %s 与 range 不符' % (gw, qids))
            if qr and not (qr[0] <= a and b <= qr[1]):
                rep.err('%s 超出 part 的 questions_range %s' % (gw, qr))
            ids += qids
            okeys = {o['key'] for o in g.get('options', [])}
            limit = g.get('limit')
            placeholders = set()
            for src in [g.get('template', '')] + [q.get('prompt', '') for q in qs]:
                for n, k in PH.findall(src or ''):
                    placeholders.add((int(n), int(k) if k else None))
            for q in qs:
                qw = 'Q%s' % q.get('id')
                ans = q.get('answer')
                if t == 'multi_choice':
                    continue
                if not ans:
                    rep.err('%s 没有答案' % qw)
                    continue
                if t in ('tfng', 'ynng'):
                    allowed = TFNG if t == 'tfng' else YNNG
                    if len(ans) != 1 or ans[0] not in allowed:
                        rep.err('%s 判断题答案应为 %s 之一（全大写全称），实际 %r' % (qw, '/'.join(sorted(allowed)), ans))
                elif t == 'single_choice':
                    keys = {o['key'] for o in q.get('options', [])}
                    if not keys:
                        rep.err('%s 单选题缺少 options' % qw)
                    elif any(x not in keys for x in ans):
                        rep.err('%s 答案 %r 不在选项 %s 中' % (qw, ans, sorted(keys)))
                elif t == 'matching':
                    if not okeys:
                        rep.err('%s 配对题组缺少 options' % gw)
                    elif any(x not in okeys for x in ans):
                        rep.err('%s 答案 %r 不在选项中' % (qw, ans))
                    if g.get('select_inline') and not any(n == q['id'] for n, _ in placeholders):
                        rep.err('%s 是 select_inline，但模板里没有 {{%s}}' % (qw, q['id']))
                elif t == 'completion':
                    blanks = q.get('blanks', 1)
                    if blanks > 1:
                        if len(ans) != blanks or not all(isinstance(x, list) and x for x in ans):
                            rep.err('%s blanks=%d，answer 需为 %d 组列表' % (qw, blanks, blanks))
                        for k in range(1, blanks + 1):
                            if (q['id'], k) not in placeholders:
                                rep.err('%s 缺少空位 {{%s.%s}}' % (qw, q['id'], k))
                        flat = [x for grp in ans if isinstance(grp, list) for x in grp]
                    else:
                        if not all(isinstance(x, str) and x.strip() for x in ans):
                            rep.err('%s 答案必须是非空字符串列表' % qw)
                            continue
                        if (q['id'], None) not in placeholders:
                            rep.err('%s 模板 / prompt 里缺少空位 {{%s}}' % (qw, q['id']))
                        flat = ans
                    if limit:
                        for x in flat:
                            n = count_words(x, limit.get('number'))
                            if n > limit.get('words', 99):
                                rep.err('%s 标准答案 %r 有 %d 个词，超过字数限制 %d' % (qw, x, n, limit['words']))
                if module == 'listening' and 't' in q and not isinstance(q['t'], (int, float)):
                    rep.err('%s 的 t 必须是秒数' % qw)
                ev = q.get('evidence')
                if ev and module == 'reading' and ev not in passage:
                    rep.err('%s evidence 在原文中找不到：%r' % (qw, ev[:60]))
            if t == 'multi_choice':
                aset = g.get('answer_set') or []
                if len(aset) != len(qs):
                    rep.err('%s 多选题 answer_set 有 %d 个，但小题有 %d 个' % (gw, len(aset), len(qs)))
                if any(x not in okeys for x in aset):
                    rep.err('%s answer_set %r 不在选项中' % (gw, aset))
            if t == 'completion' and limit is None:
                rep.warn('%s 填空题没有 limit（不会做字数检查）' % gw)
            extra = {n for n, _ in placeholders} - set(range(a, b + 1))
            if extra:
                rep.err('%s 模板里有不属于本组的空位 %s' % (gw, sorted(extra)))
    if sorted(ids) != list(range(1, 41)):
        dup = sorted({i for i in ids if ids.count(i) > 1})
        missing = sorted(set(range(1, 41)) - set(ids))
        rep.err('全卷题号应为 1–40：缺 %s，重复 %s' % (missing, dup))
    if not d.get('verified'):
        rep.warn('verified=false（界面会显示“未核对”）')
    return rep


def main(argv):
    strict = '--strict' in argv
    targets = [a for a in argv if not a.startswith('--')]
    data_dir = os.path.join(ROOT, 'ielts_client', 'data')
    media = None
    try:
        sys.path.insert(0, os.path.join(ROOT, 'ielts_client'))
        from app import load_config
        from media import MediaLibrary
        cfg = load_config()
        media = MediaLibrary(cfg['audio_dirs'], cfg['media_dir'])
        data_dir = cfg['data_dir']
    except Exception as e:  # 校验题库本身不依赖音频
        print('（跳过音频检查：%s）' % e)
    files = []
    for book in sorted(os.listdir(data_dir)):
        bdir = os.path.join(data_dir, book)
        if not os.path.isdir(bdir):
            continue
        for test in sorted(os.listdir(bdir)):
            if targets and '%s/%s' % (book, test) not in targets and book not in targets:
                continue
            for m in ('listening', 'reading'):
                fp = os.path.join(bdir, test, m + '.json')
                if os.path.isfile(fp):
                    files.append(fp)
    n_err = n_warn = 0
    for fp in files:
        rep = validate(fp, media)
        n_err += len(rep.errors)
        n_warn += len(rep.warnings)
        status = '✗' if rep.errors else ('!' if rep.warnings else '✓')
        print('%s %s' % (status, rep.name))
        for e in rep.errors:
            print('    错误：' + e)
        for w in rep.warnings:
            print('    提醒：' + w)
    print('\n共 %d 个文件，%d 个错误，%d 个提醒。' % (len(files), n_err, n_warn))
    return 1 if n_err or (strict and n_warn) else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
