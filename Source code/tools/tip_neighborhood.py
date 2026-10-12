"""Print UTF-16 runs with offsets in a narrow window around the known tip,
to identify the contiguous tip array."""
import re

GAME = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\Managed\Game.dll'
blob = open(GAME, 'rb').read()
anchor = blob.find('wrench icon'.encode('utf-16-le'))
RUN = re.compile(rb'(?:[\x20-\x7e]\x00){10,}')

for lo, hi, label in [(anchor - 6000, anchor + 6000, 'narrow')]:
    print('=== %s window (anchor 0x%X) ===' % (label, anchor))
    seg = blob[lo:hi]
    for m in RUN.finditer(seg):
        off = lo + m.start()
        s = m.group().decode('utf-16-le')
        print('  0x%07X  %s' % (off, s[:120]))
