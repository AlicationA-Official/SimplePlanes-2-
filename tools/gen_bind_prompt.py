"""生成按键绑定提示的完整译文。

提示是运行时拼的：
  键盘： "Press a key to assign it to\\n" + "<color=#ffff00>" + 动作名 + "</color>"
         + "\\n\\nModifier keys may also be used. To assign a modifier key alone, hold it down for 1 second."
  手柄： "Now press a button or move an axis to assign it to\\n" + "<color=#ffff00>" + 动作名 + "</color>"

插件只能整串精确匹配，所以按动作名逐个生成词条（动作名取词表里已有的中文译名，
未翻译的则沿用英文，保证仍然能匹配）。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_action_names import parse_strings  # noqa: E402

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\resources.assets'
DICT = os.path.join(WS, 'patch', 'zh-CN.json')
OUT = os.path.join(WS, 'patch', 'gap_fill_bindprompt.json')

LAST_ACTION = 'Toggle Part Outline Visibility'
KB_EN = ('Press a key to assign it to\n<color=#ffff00>{0}</color>\n\n'
         'Modifier keys may also be used. To assign a modifier key alone, hold it down for 1 second.')
KB_CN = ('按下一个按键，将其分配给\n<color=#ffff00>{0}</color>\n\n'
         '也可以使用修饰键。若要单独分配修饰键，请按住 1 秒。')
PAD_EN = 'Now press a button or move an axis to assign it to\n<color=#ffff00>{0}</color>'
PAD_CN = '现在按下按钮或移动轴，将其分配给\n<color=#ffff00>{0}</color>'


def action_names():
    """Rewired 动作表：从 'RewiredConsts' 之后开始，到最后一个动作名为止。"""
    blob = open(ASSETS, 'rb').read()
    end = blob.find(b'Toggle Part Outline Visibility')
    start = blob.rfind(b'RewiredConsts', 0, end)
    pairs = parse_strings(blob, start, end + 0x100)

    def ok(s):
        if len(s) < 3 or s in ('RewiredConsts',):
            return False
        if re.search(r'(\.|/|_|^[a-z]|\d{3,})', s):
            return False
        if re.match(r'^[0-9a-fA-F-]{16,}$', s):
            return False
        # 内部名（CamelCase）排除；保留 'VTOL' 这类全大写短词
        if ' ' not in s and re.search(r'[A-Z]', s[1:]):
            return False
        return True

    names = []
    for _off, s in pairs:
        if ok(s):
            names.append(s)
        if s == LAST_ACTION:
            break
    return names


def main():
    j = json.load(open(DICT, encoding='utf-8-sig'))
    entries = dict(j['entries'])
    for e in j['contextEntries']:
        entries.setdefault(e['key'], e['value'])

    names = action_names()
    uniq = []
    for n in names:
        if n not in uniq:
            uniq.append(n)
    print('动作显示名: %d 个（去重后 %d）' % (len(names), len(uniq)))

    out = {}
    for n in uniq:
        # 行标签可能被 contextEntries 按场景改写，凡是可能的译法都生成一份
        cands = []
        if n in entries:
            cands.append(entries[n])
        for e in j['contextEntries']:
            if e['key'] == n and e['value'] not in cands:
                cands.append(e['value'])
        if not cands:
            cands.append(n)
        for cn in cands:
            out[KB_EN.format(cn)] = KB_CN.format(cn)
            out[PAD_EN.format(cn)] = PAD_CN.format(cn)

    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('生成词条: %d 条 -> %s' % (len(out), OUT))
    print()
    print('样例:')
    for k in list(out)[:2]:
        print('  %r' % k)
        print('   ->  %r' % out[k])
    print()
    untranslated = [n for n in uniq if n not in entries]
    print('动作名本身未翻译的（仅包头尾）: %d 个，例: %s' % (len(untranslated), untranslated[:8]))


if __name__ == '__main__':
    main()
