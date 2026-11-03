"""Validate published source coverage and editorial timestamp evidence."""
import argparse
import json
import pathlib

root = pathlib.Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--complete', action='store_true', help='Require all downloaded sources to have ASR and editorial notes')
args = parser.parse_args()
load = lambda path: json.loads((root / path).read_text())
manifest = load('data/manifest.json')
ids = {item['id'] for item in manifest}
assert len(ids) == len(manifest), 'Duplicate source IDs'
downloads = load('data/download-status.json')
downloaded = {item['id'] for item in downloads if item['status'] == 'ok'}
assert downloaded <= ids, 'Download missing from manifest'
raw_paths = list((root / 'transcripts/raw').glob('*.json'))
raw = {path.stem: json.loads(path.read_text()) for path in raw_paths}
texts = {path.stem for path in (root / 'transcripts/text').glob('*.md')}
assert set(raw) == texts, 'Raw/text transcript coverage mismatch'
assert set(raw) <= downloaded, 'Transcript without verified download'
editorial = load('data/editorial-summaries.json')
assert set(editorial) <= set(raw), 'Editorial summary without real ASR'
for source, transcript in raw.items():
    assert transcript['id'] == source
    previous_start = -1.0
    for segment in transcript['segments']:
        assert 0 <= segment['start'] <= segment['end'] <= transcript['duration'] + 0.5, source
        assert segment['start'] >= previous_start, source
        previous_start = segment['start']
for source, entry in editorial.items():
    assert entry['overview'].strip() and entry['limits'].strip(), source
    end = max((segment['end'] for segment in raw[source]['segments']), default=0)
    for point in entry['points']:
        assert 0 <= point['start'] <= point['end'] <= end + 0.1, (source, point)
        assert point['text'].strip(), source
    note = (root / f'notes/{source}.md').read_text()
    assert entry['overview'] in note, f'Published editorial missing: {source}'
    assert f'https://www.douyin.com/video/{source}' in note, source
for item in manifest:
    assert item['asr_status'] == ('done' if item['id'] in raw else 'pending'), item['id']
status = load('data/status.json')
assert status['collected'] == len(ids)
assert status['downloaded'] == len(downloaded)
assert status['asr_completed'] == len(raw)
if args.complete:
    assert downloaded == set(raw) == set(editorial), 'Downloaded source coverage incomplete'
print(json.dumps({'sources': len(ids), 'downloaded': len(downloaded), 'asr': len(raw), 'editorial': len(editorial), 'remaining_asr': len(downloaded - set(raw)), 'remaining_editorial': len(downloaded - set(editorial)), 'complete': downloaded == set(raw) == set(editorial)}, ensure_ascii=False))
