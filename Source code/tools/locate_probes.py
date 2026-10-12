"""Locate the sources of the strings shown in the user's screenshots."""
import os
import re

DATA = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data'
PROBES = [
    b'Teleport Up',
    b'Damage Visualizer',
    b'Toggles the foam on the water surface',
    b'Tip: Several parts have properties',
    b'Recenter view',
]

for dp, dn, fn in os.walk(DATA):
    for f in fn:
        p = os.path.join(dp, f)
        if os.path.getsize(p) > 1200 * 1024 * 1024:
            continue
        try:
            blob = open(p, 'rb').read()
        except OSError:
            continue
        for probe in PROBES:
            n = blob.count(probe)
            if n:
                i = blob.find(probe)
                seg = re.sub(rb'[^\x20-\x7e]', b'.', blob[max(0, i - 120):i + 160]).decode('latin1')
                print('[%s] %-24s x%d' % (os.path.relpath(p, DATA), probe.decode(), n))
                print('     ...%s...' % seg)
