import json,pathlib,re,collections,datetime
R=pathlib.Path(__file__).resolve().parents[1]
items=json.loads((R/'data/manifest-raw.json').read_text()); statuses=json.loads((R/'data/download-status.json').read_text());status={x['id']:x for x in statuses}
(R/'notes').mkdir(exist_ok=True)
clean=[];rows=[]
editorial_path=R/'data/editorial-summaries.json'
editorial=json.loads(editorial_path.read_text()) if editorial_path.exists() else {}
for v in items:
 i=v['aweme_id']; raw=R/f'transcripts/raw/{i}.json';trans=json.loads(raw.read_text()) if raw.exists() else None
 clean.append({'id':i,'title':v['desc'],'url':f'https://www.douyin.com/video/{i}','published_timestamp':v['create_time'],'duration_seconds':status[i]['duration'],'download_status':status[i]['status'],'asr_status':'done' if trans else 'pending','segments':len(trans['segments']) if trans else None})
 note=f"# {v['desc']}\n\n来源：https://www.douyin.com/video/{i}\n\n"
 if trans and i in editorial:
  e=editorial[i]
  note+='## 基于完整机器转写的中文摘要\n\n'+e['overview']+'\n\n'
  for point in e['points']:
   note+=f"- [{point['start']:.2f}–{point['end']:.2f}秒] {point['text']}\n"
  note+='\n### 证据与限制\n\n'+e['limits']+'\n\n摘要为编辑性归纳，原始ASR未改写；讲者观点、宣传和举例不代表独立核验事实。\n'
  note+=f'\n[完整带时间轴机器转写](../transcripts/text/{i}.md) · [原始ASR JSON](../transcripts/raw/{i}.json)\n'
 elif trans:
  segments=trans['segments'];note+='## 机器转写摘录（非人工摘要）\n\n以下按时间顺序选取信息量较高的语段，保留ASR原始措辞，可能存在同音字、专名或术语错误。不能将营销口述视为独立核验事实。\n\n'
  # Deterministic extractive notes, never manufacture spoken content.
  candidates=[]
  for j,s in enumerate(segments):
   score=sum(len(m.group()) for m in re.finditer('企业|经营|价值|成本|需求|问题|战略|业务|数据|落地|投资|回报|能力|合作|项目',s['text']))+min(len(s['text']),25)/10
   if len(s['text'])>=10:candidates.append((score,j))
  chosen=sorted(j for _,j in sorted(candidates,reverse=True)[:4])
  if not segments:note+='ASR未检测到可转写语音；这不等于已人工确认视频完全无语音。\n'
  for j in chosen:
   s=segments[j];note+=f"- [{s['start']:.2f}–{s['end']:.2f}秒] {s['text']}\n"
  note+=f'\n[完整带时间轴机器转写](../transcripts/text/{i}.md) · [原始ASR JSON](../transcripts/raw/{i}.json)\n'
 else:note+='实际媒体已下载并提取音频；ASR处理中。未根据标题生成内容摘要。\n'
 (R/f'notes/{i}.md').write_text(note)
 rows.append(f"| {i} | {v['desc'].replace('|','/')[:90]} | {status[i]['duration']:.1f} | {'已完成' if trans else '处理中'} | [笔记](notes/{i}.md) |")
(R/'data/manifest.json').write_text(json.dumps(clean,ensure_ascii=False,indent=2))
report={'expected_public_count':108,'collected':len(items),'downloaded':sum(x['status']=='ok' for x in statuses),'audio_extracted':sum((R/f"media/audio/{x['id']}.wav").exists() for x in statuses),'asr_completed':sum((R/f"transcripts/raw/{x['id']}.json").exists() for x in statuses),'unavailable_due_to_login':108-len(items),'downloaded_duration_seconds':sum(x.get('duration',0) for x in statuses),'video_bytes':sum(x.get('bytes',0) for x in statuses),'audio_bytes':sum(f.stat().st_size for f in (R/'media/audio').glob('*.wav')),'blocker':'API not_login_module.guide_login_tip_exist=true; first-page has_more=1; next-page only returns status_code=0 without aweme_list; no saved browser login','asr_model':'faster-whisper-small int8 CPU zh','updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(R/'data/status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
README=f'''# 小智_企业AI落地：视频与真实转写笔记

## 完成度（明确未完成全量）

- 账号：小智_企业AI落地，抖音号 91253042124。
- 用户提供主页作品数：108；实际取得唯一作品 **{len(items)}**。
- 已下载并以 ffprobe 验证视频 **{report['downloaded']}**，ffmpeg 提取16kHz单声道音频 **{report['audio_extracted']}**。
- 实际中文ASR已完成 **{report['asr_completed']}**；其余已下载音频仍在处理中。
- 已下载媒体总时长 **{report['downloaded_duration_seconds']:.3f} 秒**。
- 未取得 **{108-len(items)}** 条：平台明确返回需登录查看更多作品。不是下载失败，不知道这些条目的ID，不能伪造完整清单。

## 访问限制证据

公开首屏API count=108只返回38条，has_more=1，附带 not_login_module.guide_login_tip_exist=true、提示“看更多最新作品”；翻页返回 `{{"status_code":0}}`，没有 aweme_list。浏览器凭据库没有已保存登录。需要用户在当前GUI浏览器正常完成抖音登录后，再运行采集，不能规避验证。

## 内容可信度

`transcripts/raw/` 是对本地真实音频运行 faster-whisper-small 的原始结果，保留秒级时间轴和置信度；`transcripts/text/` 仅格式化原始转写，没有靠标题生成口播。小模型中文专名、FDE等词可能误识别，**尚未逐字人工校对**。

`notes/` 中已有 **{sum(i['id'] in editorial for i in clean)}** 条基于完整转写编写的中文摘要，包含时间戳和来源限制；其余已完成ASR的条目仍为明确标记的机器摘录。摘要存于 `data/editorial-summaries.json`，再次发布时会保留。`SUMMARY.md` 为已读转写的阶段性综合整理，不代表108条全量结论。未检测到语音时仅报告ASR检测结果，不冒充人工听辨。

## 本地媒体与仓库

视频：`media/video/<作品ID>.mp4`；音频：`media/audio/<作品ID>.wav`。媒体保留在本机，**不上传GitHub**；仓库为私有，包含脱敏索引、转写、笔记与脚本。短期CDN签名地址、完整原始API响应均被gitignore排除。

## 复现

```sh
uv venv .venv
uv pip install --python .venv/bin/python faster-whisper==1.2.1 av==16.1.0
# 先在连接opencli的浏览器正常登录抖音
python scripts/collect.py  # 108条断言未通过时明确失败，仍保留已取得数据
.venv/bin/python scripts/process.py
python scripts/publish.py
```

需要 `opencli`、`ffmpeg`、`ffprobe`、`curl`。脚本可断点续跑。锁定 av<19 避免 faster-whisper metadata_errors API兼容问题。ASR small模型需已缓存，默认不联网下载。运行ASR时用2个CPU线程避免此主机2核严重过度订阅。

## 索引

| 作品ID | 发布说明（不是转写） | 秒 | ASR | 笔记 |
|---|---|---:|---|---|
'''
(R/'README.md').write_text(README+'\n'.join(rows)+'\n')
print(json.dumps(report,ensure_ascii=False))
