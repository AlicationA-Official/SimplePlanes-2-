"""Dump the raw structure around the Rewired action-name data."""
import re

ASSETS = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\resources.assets'
blob = open(ASSETS, 'rb').read()

i = blob.find(b'Damage Visualizer')
print('index', hex(i))
seg = blob[i - 3000:i + 3000]
print(re.sub(rb'[^\x20-\x7e]', b'.', seg).decode('latin1'))
