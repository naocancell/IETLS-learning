# -*- coding: utf-8 -*-
"""
新建一套题的空白模板：python tools/new_test.py 5 1 [--general]
生成 ielts_client/data/c05/t1/listening.json 与 reading.json（verified=false），
然后按 docs/修复记录与剑5-21导入指南.md 填写题目、答案，最后运行 tools/validate_data.py。
已存在的文件不会被覆盖。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def listening(book, test):
    parts = []
    for n in range(1, 5):
        a, b = 10 * n - 9, 10 * n
        parts.append({
            'number': n, 'title': 'Part %d' % n,
            'audio': 'c%02d/t%d/s%d.mp3' % (book, test, n),
            'transcript': 'transcript_s%d.json' % n,
            'questions_range': [a, b],
            'groups': [{
                'range': [a, b], 'type': 'completion', 'category': 'note_completion',
                'instruction': 'Complete the notes below.\nWrite **ONE WORD AND/OR A NUMBER** for each answer.',
                'limit': {'words': 1, 'number': True},
                'template': '# TITLE\n\n' + '\n'.join('- ... {{%d}}' % i for i in range(a, b + 1)),
                'questions': [{'id': i, 'answer': ['TODO']} for i in range(a, b + 1)],
            }],
        })
    return {'schema_version': 2, 'book': book, 'test': test, 'module': 'listening',
            'title': 'Cambridge IELTS %d · Test %d · Listening' % (book, test), 'verified': False,
            'source': {'pdf': '题目/Cambridge-IELTS-%02d.pdf' % book, 'pages': [], 'note': ''}, 'parts': parts}


def reading(book, test, general):
    ranges = [(1, 13), (14, 26), (27, 40)] if not general else [(1, 14), (15, 27), (28, 40)]
    parts = []
    for n, (a, b) in enumerate(ranges, 1):
        parts.append({
            'number': n, 'title': 'Reading Passage %d' % n if not general else 'Section %d' % n,
            'passage_title': 'TODO', 'passage': 'TODO 段落之间空一行；带字母的段落写成 [A] 开头。',
            'questions_range': [a, b],
            'groups': [{
                'range': [a, b], 'type': 'tfng', 'category': 'tfng',
                'instruction': 'Do the following statements agree with the information given in Reading Passage %d?' % n,
                'questions': [{'id': i, 'prompt': 'TODO', 'answer': ['TRUE']} for i in range(a, b + 1)],
            }],
        })
    return {'schema_version': 2, 'book': book, 'test': test, 'module': 'reading',
            'variant': 'general' if general else 'academic',
            'title': 'Cambridge IELTS %d · Test %d · %s Reading' % (book, test, 'General Training' if general else 'Academic'),
            'verified': False, 'source': {'pdf': '题目/Cambridge-IELTS-%02d.pdf' % book, 'pages': [], 'note': ''}, 'parts': parts}


def main(argv):
    nums = [a for a in argv if not a.startswith('--')]
    if len(nums) != 2:
        print(__doc__)
        return 2
    book, test = int(nums[0]), int(nums[1])
    d = os.path.join(ROOT, 'ielts_client', 'data', 'c%02d' % book, 't%d' % test)
    os.makedirs(os.path.join(d, 'img'), exist_ok=True)
    for name, obj in (('listening', listening(book, test)), ('reading', reading(book, test, '--general' in argv))):
        fp = os.path.join(d, name + '.json')
        if os.path.exists(fp):
            print('已存在，跳过：' + os.path.relpath(fp, ROOT))
            continue
        with open(fp, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        print('已创建：' + os.path.relpath(fp, ROOT))
    return 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
