import json,subprocess,pathlib,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
(ROOT/'data/pages').mkdir(parents=True,exist_ok=True)
sec='MS4wLjABAAAAQwhxUlt8A_bsZjFYefDlNftEY7VhzOFh1a5kMK1yeqNIrjpTMiGDgtAo9xyKATfJ'
cursor=0; items={}
for n in range(20):
 url=f'https://www.douyin.com/aweme/v1/web/aweme/post/?sec_user_id={sec}&max_cursor={cursor}&count=108&aid=6383'
 expr="(async()=>{const r=await fetch("+json.dumps(url)+",{credentials:'include',headers:{'Content-Type':'application/json',referer:'https://www.douyin.com/'}});return await r.json()})()"
 out=subprocess.check_output(['opencli','browser','xiaozhi','eval',expr],text=True)
 d=json.loads(out)
 (ROOT/f'data/pages/{n:02}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
 for v in d.get('aweme_list',[]): items[v['aweme_id']]=v
 (ROOT/'data/manifest-raw.json').write_text(json.dumps(list(items.values()),ensure_ascii=False,indent=2))
 print(n,len(d.get('aweme_list',[])),len(items),d.get('max_cursor'),d.get('has_more'),flush=True)
 nxt=d.get('max_cursor')
 if not d.get('has_more') or nxt==cursor: break
 cursor=nxt;time.sleep(1)
assert len(items)==108, f'Expected 108, collected {len(items)}'
