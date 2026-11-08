"""Collect publicly listed song metadata; do not download audio or choreography."""
import json, re, datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

URL='https://japracool.com/bodycombat-tracklist/'
root=Path(__file__).resolve().parents[1]
path=root/'releases.json'
old=json.loads(path.read_text()) if path.exists() else {}
r=requests.get(URL,timeout=35,headers={'User-Agent':'Mozilla/5.0 (compatible; CombatMixTracklistUpdater/1.0)'})
r.raise_for_status()
soup=BeautifulSoup(r.text,'html.parser')
found={}
for h in soup.find_all(re.compile(r'^h[1-4]$')):
    match=re.match(r'^BODYCOMBAT\s+(\d{1,3}|UNITED)\b',h.get_text(' ',strip=True),re.I)
    if not match:continue
    release=match.group(1).upper()
    # Search forward until next release heading, avoiding unrelated tables.
    table=None
    for el in h.next_elements:
        if el is h:continue
        if getattr(el,'name',None) in ('h1','h2','h3','h4') and re.match(r'^BODYCOMBAT\s+(?:\d{1,3}|UNITED)\b',el.get_text(' ',strip=True),re.I):break
        if getattr(el,'name',None)=='table':table=el;break
    if table is None:continue
    tracks=[]
    for row in table.find_all('tr'):
        cells=[x.get_text(' ',strip=True) for x in row.find_all('td',recursive=False)]
        if len(cells)<3:continue
        label,title,artist=cells[:3]
        m=re.search(r'\d{1,2}',label)
        if not m or not re.match(r'^(?:\d|bonus|alt)',label,re.I):continue
        slot=int(m.group())-1
        if not 0<=slot<=9 or not title or not artist:continue
        tracks.append({'number':label,'slot':slot,'title':title,'artist':artist,'duration':''})
    if len(tracks)>=7 and len({t['slot'] for t in tracks})>=6:
        found[release]={'tracks':tracks,'source':URL,'importedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
if len(found)<50:
    raise RuntimeError(f'Only {len(found)} valid release tables found; refusing to publish incomplete data. Check archive layout.')
for key,release in found.items():old[key]=release
path.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
print(f'Published {len(found)} releases, {sum(len(v["tracks"]) for v in found.values())} tracks')
