"""Find the source of part-list group headers (e.g. 'Main Landing Gear')."""
import re

ASSETS = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\resources.assets'

blob = open(ASSETS, 'rb').read()

i = blob.find(b'Main Landing Gear')
print('=== context around "Main Landing Gear" ===')
print(re.sub(rb'[^\x20-\x7e]', b'.', blob[i - 350:i + 250]).decode('latin1'))
print()

for attr in (b'subCategory', b'subcategory', b'sub-header', b'subHeader', b'header'):
    vals = sorted({m.decode() for m in re.findall(attr + rb'="([^"]+)"', blob)})
    if vals:
        print('%s values (%d):' % (attr.decode(), len(vals)))
        for v in vals:
            print('   ', v)
        print()
