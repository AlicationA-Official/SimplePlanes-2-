"""Extract data-driven UI XML documents from a Unity resources.assets file
and pull out user-facing text attributes."""
import os
import re
import sys

ASSETS = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\resources.assets'
OUTDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'ui_xml')

ATTRS = re.compile(rb'(text|tooltip|title|label|placeholder|description|displayName)\s*=\s*"([^"]*)"')


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    data = open(ASSETS, 'rb').read()
    print('resources.assets size:', len(data))
    starts = [m.start() for m in re.finditer(rb'<Xml[ >]', data)]
    print('found %d "<Xml" markers' % len(starts))
    docs = []
    for i, s in enumerate(starts):
        # cut at the last </Xml> before the next marker
        end_limit = starts[i + 1] if i + 1 < len(starts) else min(len(data), s + 8 * 1024 * 1024)
        window = data[s:end_limit]
        e = window.rfind(b'</Xml>')
        if e < 0:
            continue
        blob = window[:e + 6]
        docs.append((s, blob))
    print('recovered %d complete XML documents' % len(docs))
    total = 0
    for idx, (off, blob) in enumerate(docs):
        name = 'doc_%02d_0x%X.xml' % (idx, off)
        open(os.path.join(OUTDIR, name), 'wb').write(blob)
        hits = ATTRS.findall(blob)
        total += len(hits)
        print('  %-26s %8d bytes  %4d text attrs' % (name, len(blob), len(hits)))
    print('total text attributes:', total)


if __name__ == '__main__':
    main()
