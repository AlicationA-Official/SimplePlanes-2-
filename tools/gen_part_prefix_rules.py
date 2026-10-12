"""生成"零件名前缀规则"。

放置到飞行器上的零件，其列表标签是运行时拼接的：
    "Military Jet Engine  <color=#ffffff50><size=90%>#2"
以及删除提示：
    "Deleted Exhaust #6 and 6 other parts"

插件只能整串精确匹配，所以为每个零件显示名生成一条"前缀规则"，
这样上面两种拼接串都能被翻译（精确词条优先级更高，不会互相干扰）。
"""
import json
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\resources.assets'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')
OUT = os.path.join(WS, 'patch', 'gap_fill_partname_prefix.json')

CJK = re.compile(r'[\u3000-\u9fff]')


def main():
    blob = open(ASSETS, 'rb').read()
    names = []
    for m in re.finditer(rb'<DesignerPart\s+name="([^"]{2,60})"', blob):
        n = m.group(1).decode('utf-8', 'replace')
        if n not in names:
            names.append(n)
    print('零件名: %d 个' % len(names))

    j = json.load(open(DICT, encoding='utf-8-sig'))
    entries = j['entries']
    ctx = {}
    for e in j['contextEntries']:
        # 优先 /PartButton-<name>/ 这种零件按钮路径
        if 'PartButton' in (e.get('gameObjectPathContains') or ''):
            ctx.setdefault(e['key'], e['value'])

    rules, skipped = [], []
    for n in names:
        cn = ctx.get(n) or entries.get(n)
        if not cn or not CJK.search(cn) or cn == n:
            skipped.append(n)
            continue
        if len(n) < 4:          # 太短的前缀容易误伤
            skipped.append(n)
            continue
        # 删除提示是 "Deleted <零件名> #n and N other parts"
        rules.append({'sourcePrefix': 'Deleted ' + n,
                      'valuePrefix': '已删除 ' + cn, 'valueSuffix': ''})
        rules.append({'sourcePrefix': n, 'valuePrefix': cn, 'valueSuffix': ''})

    # 长的优先，避免短前缀抢先匹配
    rules.sort(key=lambda r: -len(r['sourcePrefix']))
    json.dump({'dynamicPrefixEntries': rules},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('生成前缀规则: %d 条 -> %s' % (len(rules), OUT))
    print('跳过（无译文/过短）: %d 条，例: %s' % (len(skipped), skipped[:8]))
    for r in rules[:5]:
        print('   %-28s -> %s' % (r['sourcePrefix'], r['valuePrefix']))


if __name__ == '__main__':
    main()
