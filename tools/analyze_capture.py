"""分析插件采集结果，按优先级分类未翻译文本。

分桶：
  A 句子   —— 含空格且长度 >= 24，或带句末标点：几乎肯定是界面文案/教程正文
  B 短语   —— 含空格、较短：标签或下拉选项
  C 单词   —— 不含空格：多为数据值（零件名/预制体名/枚举值）或制作人员名字
"""
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2'
CAP = os.path.join(GAME, 'BepInEx', 'plugins', 'SimplePlanes2Translation', 'captured-texts.json')
DICT = os.path.join(WS, 'patch', 'zh-CN.json')
OUT = os.path.join(WS, 'data', 'capture_buckets.txt')

CJK = re.compile(r'[\u3000-\u9fff\uff00-\uffef]')
SKIP = re.compile(r'^[\s\d\W_]*$')
BINDING = re.compile(r'\{[^}]*\}')
DATAISH = re.compile(r'^(?:[A-Za-z0-9_\-\.]+|[\d\s\.,;:\-+*/()]+)$')


def main():
    j = json.load(open(DICT, encoding='utf-8-sig'))
    tr = set(j['entries']) | {e['key'] for e in j['contextEntries']}
    pre = [e['sourcePrefix'] for e in j.get('dynamicPrefixEntries', [])]
    suf = [e['sourceSuffix'] for e in j.get('dynamicSuffixEntries', [])]

    def covered(t):
        if t in tr:
            return True
        for p in pre:
            if p and t.startswith(p):
                return True
        for s in suf:
            if s and t.endswith(s):
                return True
        return False

    items = json.load(open(CAP, encoding='utf-8-sig'))

    buckets = {'A': [], 'B': [], 'C': [], 'credits': []}
    for it in items:
        t = (it.get('Text') or '').strip()
        if not t or CJK.search(t) or covered(t) or SKIP.match(t) or BINDING.search(t):
            continue
        ctxs = it.get('Contexts') or []
        paths = sorted({(c.get('SceneName') or '?', c.get('GameObjectPath') or '') for c in ctxs})
        scenes = ','.join(sorted(set(it.get('Scenes') or [])))
        loc = ' ;; '.join('%s|%s' % (s, p[-70:]) for s, p in paths[:2])
        row = '[%s] %s  <<%s>>' % (scenes, t.replace('\n', '\\n'), loc)
        if any(re.search(r'redit|ontributor|Staff', p) for _s, p in paths):
            buckets['credits'].append(row)
        elif len(t) >= 24 and ' ' in t or re.search(r'[.!?。！？]$', t):
            buckets['A'].append(row)
        elif ' ' in t:
            buckets['B'].append(row)
        else:
            buckets['C'].append(row)

    with open(OUT, 'w', encoding='utf-8') as f:
        for k, title in [('A', '句子（最可能是未翻译文案）'),
                         ('B', '短语（标签/选项）'),
                         ('C', '单词（多为数据值/预制体名）'),
                         ('credits', '制作人员名单')]:
            f.write('\n===== %s: %d 条 =====\n' % (title, len(buckets[k])))
            f.write('\n'.join(sorted(buckets[k])))
            f.write('\n')
    print('A 句子 %d | B 短语 %d | C 单词 %d | 名单 %d' %
          (len(buckets['A']), len(buckets['B']), len(buckets['C']), len(buckets['credits'])))
    print('written %s' % OUT)
    print()
    print('===== A 类（句子）=====')
    for l in sorted(buckets['A']):
        print('  ', l)


if __name__ == '__main__':
    main()
