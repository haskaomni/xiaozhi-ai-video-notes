import pathlib,json,subprocess,concurrent.futures,time
R=pathlib.Path(__file__).resolve().parents[1]
for p in ['media/video','media/audio','transcripts/raw','transcripts/text','logs']: (R/p).mkdir(parents=True,exist_ok=True)
items=json.loads((R/'data/manifest-raw.json').read_text())
def get(v):
 i=v['aweme_id']; video=R/f'media/video/{i}.mp4';audio=R/f'media/audio/{i}.wav'
 try:
  if not video.exists(): subprocess.run(['curl','-fL','--retry','3','-A','Mozilla/5.0','-e','https://www.douyin.com/','-o',str(video),v['video']['play_addr']['url_list'][0]],check=True,capture_output=True)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(video)]))
  if not audio.exists():subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vn','-ac','1','-ar','16000',str(audio)],check=True,capture_output=True)
  return {'id':i,'status':'ok','duration':float(probe['format']['duration']),'bytes':video.stat().st_size}
 except Exception as e:return {'id':i,'status':'failed','error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 results=list(pool.map(get,items))
(R/'data/download-status.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('DOWNLOAD',len(results),sum(x['status']=='ok' for x in results),flush=True)
from faster_whisper import WhisperModel
model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=2,local_files_only=True)
for s in results:
 if s['status']!='ok':continue
 i=s['id'];target=R/f'transcripts/raw/{i}.json'
 if target.exists():continue
 started=time.time()
 try:
  seg,info=model.transcribe(str(R/f'media/audio/{i}.wav'),language='zh',beam_size=1,vad_filter=True)
  data=[{'start':x.start,'end':x.end,'text':x.text,'avg_logprob':x.avg_logprob,'no_speech_prob':x.no_speech_prob} for x in seg]
  target.write_text(json.dumps({'id':i,'model':'faster-whisper-small','language':'zh','duration':info.duration,'segments':data},ensure_ascii=False,indent=2))
  (R/f'transcripts/text/{i}.md').write_text('# '+i+'\n\n机器原始转写，未经逐字人工校对。\n\n'+'\n'.join(f"[{x['start']:.2f}–{x['end']:.2f}] {x['text']}" for x in data))
  print('ASR',i,len(data),round(time.time()-started,1),flush=True)
 except Exception as e: print('ASR_FAIL',i,str(e),flush=True)
