# -*- coding: utf-8 -*-
"""
听力录音 → 带时间戳的原文（transcript_sN.json），并自动定位每题答案出现的时间（q.t）。

安装：pip install -r requirements-tools.txt   （faster-whisper；另需 ffmpeg 在 PATH 中更稳）
用法：
  python tools/transcribe.py c05/t1                 转写 4 段并写入 data/c05/t1/transcript_s*.json
  python tools/transcribe.py c05/t1 --locate        只根据已有原文重新定位答案时间
  python tools/transcribe.py c05/t1 --model medium.en   用更大的模型（更准、更慢）

说明：
  * 这是语音识别结果，不是官方 Tapescript；书后有 Tapescript 时请以书为准
    （可以把书上的文字按句粘进 segments[].text，保留 start/end 即可）。
  * --locate 按答案文本在原文里查找，找不到的题会列出来，请手动填写 t（秒）。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'ielts_client'))

from app import load_config  # noqa: E402
from media import MediaLibrary  # noqa: E402


def load_audio(path):
    """用 ffmpeg 解码为 16k 单声道（绕开部分 PyAV 版本读 mp3 元数据报错的问题）。"""
    if not shutil.which('ffmpeg'):
        return path
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 's16le', '-ac', '1', '-ar', '16000', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def norm(s):
    s = s.lower().replace('’', "'").replace('-', ' ')
    s = re.sub(r'[^a-z0-9£$%\' ]+', ' ', s)
    return ' '.join(s.split())


NUM_WORDS = {'12': 'twelve', '13th': 'thirteenth', '160': 'hundred and sixty'}


def candidates(q):
    out = []
    ans = q.get('answer') or []
    flat = [x for grp in ans for x in (grp if isinstance(grp, list) else [grp])]
    for a in flat:
        a = re.sub(r'\(([^)]*)\)', '', str(a)).strip()   # 去掉 (the) 之类可省略部分
        if len(a) <= 1 and a.isalpha() and a.isupper():
            continue  # 选择题字母无法在原文里定位
        out.append(norm(a))
        out += [norm(NUM_WORDS[w]) for w in a.split() if w in NUM_WORDS]
        if re.fullmatch(r'\d+', a):
            out.append(norm(f'{int(a):,}'))
        m = re.fullmatch(r'(\d+(?:st|nd|rd|th)) (\w+)', a)
        if m:  # 13th February → 13th of February
            out.append(norm(m.group(1) + ' of ' + m.group(2)))
    return [c for c in out if c]


def locate(data, base, force=False):
    found, missing = 0, []
    for part in data['parts']:
        tfile = os.path.join(base, part.get('transcript') or '')
        if not part.get('transcript') or not os.path.isfile(tfile):
            continue
        with open(tfile, encoding='utf-8') as f:
            segs = json.load(f)['segments']
        texts = [norm(s['text']) for s in segs]
        cursor = 0
        for g in part['groups']:
            for q in g['questions']:
                if 't' in q and not force:
                    cursor = max(cursor, _seg_at(segs, q['t']))
                    continue
                cands = candidates(q)
                hit = None
                for i in range(cursor, len(segs)):
                    nxt = texts[i + 1] if i + 1 < len(segs) else ''
                    window = texts[i] + ' ' + nxt
                    # 答案在本句内，或跨越本句与下一句的边界
                    if any(c in texts[i] or (c in window and c not in nxt) for c in cands):
                        hit = i
                        break
                if hit is None:
                    missing.append(q['id'])
                    continue
                q['t'] = segs[hit]['start']
                cursor = hit  # 题目顺序 = 录音顺序
                found += 1
    return found, missing


def _seg_at(segs, t):
    idx = 0
    for i, sg in enumerate(segs):
        if sg['start'] <= t + 0.5:
            idx = i
    return idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('test', help='如 c05/t1')
    ap.add_argument('--model', default='small.en')
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--compute-type', default='int8')
    ap.add_argument('--locate', action='store_true', help='只重新定位答案时间')
    ap.add_argument('--force', action='store_true', help='覆盖已有的 t（默认只补空缺）')
    args = ap.parse_args()

    cfg = load_config()
    base = os.path.join(cfg['data_dir'], *args.test.split('/'))
    lpath = os.path.join(base, 'listening.json')
    with open(lpath, encoding='utf-8') as f:
        data = json.load(f)

    if not args.locate:
        from faster_whisper import WhisperModel
        lib = MediaLibrary(cfg['audio_dirs'], cfg['media_dir'])
        model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
        for part in data['parts']:
            audio = lib.ensure(part['audio'])
            if not audio:
                print('找不到音频 %s，跳过' % part['audio'])
                continue
            print('转写 Part %s …' % part['number'], flush=True)
            segs, _info = model.transcribe(load_audio(audio), language='en', beam_size=5, vad_filter=True)
            out = [{'start': round(s.start, 2), 'end': round(s.end, 2), 'text': s.text.strip()} for s in segs]
            part.setdefault('transcript', 'transcript_s%d.json' % part['number'])
            with open(os.path.join(base, part['transcript']), 'w', encoding='utf-8') as f:
                json.dump({'source': 'asr', 'model': 'faster-whisper ' + args.model,
                           'note': '自动语音识别结果，未人工校对；以官方 Tapescript 为准。', 'segments': out},
                          f, ensure_ascii=False, indent=1)

    found, missing = locate(data, base, args.force)
    with open(lpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('新定位 %d 题的答案时间（已有 t 的题保持不变，--force 可覆盖）。' % found)
    if missing:
        print('未能自动定位（选择/配对题或识别有误，请手动填写 t）：' + ', '.join(map(str, missing)))


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
