# -*- coding: utf-8 -*-
"""
从剑桥雅思 PDF 中提取文字 / 页面图片，辅助录入题库。

安装：pip install -r requirements-tools.txt   （PyMuPDF）
用法：
  python tools/pdf_extract.py 题目/Cambridge-IELTS-05.pdf
      → work/c05/pages/p001.txt …（每页文字，已合并断词）
      → work/c05/index.txt（每个 Test / LISTENING / READING PASSAGE / Answer key / Tapescript 所在页）
  python tools/pdf_extract.py 题目/Cambridge-IELTS-05.pdf --render 12-15
      → work/c05/pages/p012.png …（150dpi 页面图，用来对照排版、截取图表）
  python tools/pdf_extract.py 题目/Cambridge-IELTS-05.pdf --crop 14 60,300,540,620 ielts_client/data/c05/t1/img/l_s2_map.png
      → 按 PDF 坐标（pt，左上角为原点）截取一块区域，保存为题目图片

注意：
  * 扫描版 PDF 没有文字层，只能看图手动录入（或先做 OCR）。
  * 网上流传的不少版本是重新排版 / 手打的，常有错别字、漏句（剑4 就是这样），
    且未必带答案和录音原文。务必与原书扫描页或官方答案核对。
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MARKERS = [
    ('Test', re.compile(r'^\s*Test\s+([1-4A-B])\s*$', re.M)),
    ('LISTENING', re.compile(r'^\s*LISTENING\s*$', re.M)),
    ('SECTION/PART', re.compile(r'^\s*(?:SECTION|PART)\s+[1-4]\b', re.M)),
    ('READING', re.compile(r'^\s*(?:ACADEMIC\s+)?READING\s*$', re.M)),
    ('READING PASSAGE', re.compile(r'READING PASSAGE\s+[1-3]', re.I)),
    ('GENERAL TRAINING', re.compile(r'GENERAL TRAINING', re.I)),
    ('WRITING', re.compile(r'^\s*WRITING\s*$', re.M)),
    ('Tapescript', re.compile(r'^\s*(?:Tapescripts?|Audioscripts?)\b', re.I | re.M)),
    ('Answer key', re.compile(r'(?:Listening and Reading )?Answer [Kk]eys?')),
]


def book_code(pdf):
    m = re.search(r'(\d{1,2})(?!.*\d)', os.path.basename(pdf))
    return 'c%02d' % int(m.group(1)) if m else os.path.splitext(os.path.basename(pdf))[0]


def page_text(page):
    blocks = page.get_text('blocks', sort=True)
    out = []
    for b in blocks:
        if b[6] != 0:  # 0 = 文字块
            continue
        t = b[4]
        t = re.sub(r'(\w)-\n(\w)', r'\1\2', t)  # 合并行尾断词
        t = re.sub(r'[ \t]*\n[ \t]*', ' ', t).strip()
        if t:
            out.append(t)
    return '\n\n'.join(out)


def parse_range(s, n):
    pages = set()
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-')
            pages.update(range(int(a), int(b) + 1))
        else:
            pages.add(int(part))
    return sorted(p for p in pages if 1 <= p <= n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('--out', help='输出目录（默认 work/<cXX>）')
    ap.add_argument('--render', help='渲染页码，如 12-15,20')
    ap.add_argument('--dpi', type=int, default=150)
    ap.add_argument('--crop', nargs=3, metavar=('PAGE', 'X0,Y0,X1,Y1', 'OUT_PNG'))
    args = ap.parse_args()

    import fitz  # PyMuPDF
    doc = fitz.open(args.pdf)
    out = args.out or os.path.join(ROOT, 'work', book_code(args.pdf))
    pages_dir = os.path.join(out, 'pages')
    os.makedirs(pages_dir, exist_ok=True)

    if args.crop:
        pno, box, dst = args.crop
        x0, y0, x1, y1 = map(float, box.split(','))
        pix = doc[int(pno) - 1].get_pixmap(dpi=200, clip=fitz.Rect(x0, y0, x1, y1))
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        pix.save(dst)
        print('已保存 %s（%dx%d）' % (dst, pix.width, pix.height))
        return

    if args.render:
        for p in parse_range(args.render, len(doc)):
            fn = os.path.join(pages_dir, 'p%03d.png' % p)
            doc[p - 1].get_pixmap(dpi=args.dpi).save(fn)
            print('渲染 ' + fn)
        return

    index = []
    empty = 0
    for i, page in enumerate(doc, 1):
        txt = page_text(page)
        if len(txt) < 30:
            empty += 1
        with open(os.path.join(pages_dir, 'p%03d.txt' % i), 'w', encoding='utf-8') as f:
            f.write(txt)
        hits = [name for name, rx in MARKERS if rx.search(txt)]
        if hits:
            first = txt.strip().split('\n')[0][:70]
            index.append('p%03d  %-60s  %s' % (i, ', '.join(hits), first))
    with open(os.path.join(out, 'index.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(index))
    print('共 %d 页，文字已写入 %s' % (len(doc), os.path.relpath(pages_dir, ROOT)))
    if empty > len(doc) * 0.5:
        print('⚠️ 超过一半页面没有文字层，可能是扫描版，需要 OCR 或手动录入。')
    print('页面索引（%s）：' % os.path.relpath(os.path.join(out, 'index.txt'), ROOT))
    print('\n'.join(index[:80]))
    if not any('Answer key' in x for x in index):
        print('⚠️ 没有找到 Answer key 页：这个 PDF 可能不含答案，需要另找官方答案核对。')
    if not any('Tapescript' in x for x in index):
        print('⚠️ 没有找到 Tapescript 页：听力原文需要用 tools/transcribe.py 语音识别生成。')


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
