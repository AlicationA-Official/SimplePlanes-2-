"""Final filter for the safe-to-key list: drop credits names, CJK leftovers,
version strings and special tokens."""
import os
import re

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\resources.assets'

CREDIT = re.compile(rb'<Instance\s+templateId="credit"\s+name="([^"]*)"\s*/>')
EXTRA_SKIP = {
    'SimpleMFD@(Newline)MENU',
    'Your Best Score: 1:18',
    'Test 23',
    'The Big L',
    'I\'ll have what they\'re having',
    'TGP OFF',          # 与已翻译的 'Targeting Pod Off' 同义，但此处是全大写 HUD 状态位
    'NAVY',
    'VFA-114',
    'CAPT KIERAN',
    '"DOKEZ"',
    'Multiplayer',      # 见下方说明：保留由 contextEntries 处理，避免与 'MULTIPLAYER SETTINGS' 冲突
}


def main():
    blob = open(ASSETS, 'rb').read()
    credits = {m.group(1).decode('utf-8', 'replace') for m in CREDIT.finditer(blob)}
    print('credits names found in assets: %d' % len(credits))

    src = os.path.join(WS, 'data', 'to_translate.txt')
    items = open(src, encoding='utf-8').read().splitlines()

    keep, dropped = [], {'cjk': 0, 'credit': 0, 'version': 0, 'extra': 0}
    for s in items:
        if re.search(r'[\u4e00-\u9fff]', s):
            dropped['cjk'] += 1
            continue
        if s in credits:
            dropped['credit'] += 1
            continue
        if re.match(r'^v?\d+(\.\d+)+$', s) or re.search(r'v\d+\.\d+\.\d+', s):
            dropped['version'] += 1
            continue
        if s in EXTRA_SKIP:
            dropped['extra'] += 1
            continue
        keep.append(s)

    out = os.path.join(WS, 'data', 'final_to_translate.txt')
    open(out, 'w', encoding='utf-8').write('\n'.join(keep))
    print('dropped: %s' % dropped)
    print('final list: %d -> %s' % (len(keep), out))
    for s in keep:
        print('   ' + s[:120])


if __name__ == '__main__':
    main()
