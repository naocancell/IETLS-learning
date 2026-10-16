# -*- coding: utf-8 -*-
"""
听力音频识别 / 准备：
  python tools/prepare_media.py --check   只查看识别结果（不复制文件）
  python tools/prepare_media.py           把题库需要的音频准备到 ielts_client/media/
  python tools/prepare_media.py --all     把识别到的所有音频都准备好

程序运行时也会在第一次播放时自动准备，一般不需要手动执行；
新增一本书时先用 --check 确认每段音频都被识别到了正确的「书/套/段」。
"""
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'ielts_client'))

from app import load_config  # noqa: E402
from media import MediaLibrary  # noqa: E402


def required_keys(data_dir):
    keys = {}
    for book in sorted(os.listdir(data_dir)) if os.path.isdir(data_dir) else []:
        if not os.path.isdir(os.path.join(data_dir, book)):
            continue
        for test in sorted(os.listdir(os.path.join(data_dir, book))):
            fp = os.path.join(data_dir, book, test, 'listening.json')
            if os.path.isfile(fp):
                with open(fp, encoding='utf-8') as f:
                    for p in json.load(f).get('parts', []):
                        if p.get('audio'):
                            keys[p['audio']] = '%s/%s' % (book, test)
    return keys


def main(argv):
    cfg = load_config()
    lib = MediaLibrary(cfg['audio_dirs'], cfg['media_dir'])
    print('音频来源：' + '，'.join(os.path.relpath(d, ROOT) for d in cfg['audio_dirs']))
    print('缓存目录：' + os.path.relpath(cfg['media_dir'], ROOT))
    by_test = defaultdict(list)
    for key, (container, member) in sorted(lib.index.items()):
        book, test, sec = key.split('/')
        src = os.path.relpath(container, ROOT) + ('::' + member if member else '')
        by_test[book + '/' + test].append((sec, src))
    print('\n识别到 %d 段音频：' % len(lib.index))
    for t in sorted(by_test):
        secs = by_test[t]
        flag = '' if len(secs) == 4 else '   ← 只有 %d 段，请检查' % len(secs)
        print('  %s: %s%s' % (t, ' '.join(s for s, _ in secs), flag))
        if '--check' in argv and '-v' in argv:
            for s, src in secs:
                print('      %s  ←  %s' % (s, src))
    if lib.duplicates:
        print('\n重复（已忽略，保留第一个）：')
        for key, label in lib.duplicates:
            print('  %s  ←  %s' % (key, label))
    if lib.unmapped:
        print('\n无法识别的文件（可在 听力/audio_map.json 手动指定）：')
        for u in lib.unmapped[:200]:
            print('  ' + u)
    req = required_keys(cfg['data_dir'])
    missing = [k for k in req if not lib.available(k)]
    print('\n题库需要 %d 段音频，缺 %d 段%s' % (len(req), len(missing), '：' if missing else '。'))
    for k in missing:
        print('  %s（%s）' % (k, req[k]))
    if '--check' in argv:
        return 1 if missing else 0
    keys = list(lib.index) if '--all' in argv else [k for k in req if k in lib.index]
    n = lib.prepare_all(keys)
    print('\n本次新准备 %d 个文件。' % n)
    return 1 if missing else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
