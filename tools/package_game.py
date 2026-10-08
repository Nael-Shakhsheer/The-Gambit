"""Build a portable source/art ZIP; checkpoints are an explicit local-only option."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile


def source_files(root, include_checkpoints=False, runtime_only=False):
    ignored={'.git','.codex','.agents','__pycache__','.venv','node_modules','releases'}
    files=[]
    for p in root.rglob('*'):
        rel=p.relative_to(root)
        if not p.is_file() or set(rel.parts)&ignored or p.suffix=='.pyc':continue
        if rel.as_posix()=='PACKAGE_MANIFEST.json':continue
        if rel.parts[0]=='data' and not (include_checkpoints and len(rel.parts)==3 and rel.parts[1]=='checkpoints' and p.suffix=='.json'):continue
        if runtime_only:
            if rel.parts[0]=='art' and (len(rel.parts)<2 or rel.parts[1]!='audio'):continue
            if rel.parts[0]=='reports' and p.suffix.lower() in ('.png','.jpg','.jpeg'):continue
        files.append((rel.as_posix(),p))
    return sorted(files)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include-checkpoints',action='store_true')
    parser.add_argument('--runtime-only',action='store_true',help='Keep playable assets and audio rebuild sources; omit large original art projects and reference screenshots.')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    now=datetime.now(timezone.utc)
    label='Playable' if args.runtime_only else 'Tactical-Update'
    output=root/'releases'/('The-Gauntlet-'+now.strftime('%Y-%m-%d-%H%M%S')+'-'+label+'.zip')
    output.parent.mkdir(exist_ok=True)
    files=source_files(root,args.include_checkpoints,args.runtime_only)
    manifest={'createdUTC':now.isoformat(),'checkpointFilesIncluded':args.include_checkpoints,'files':{}}
    prefix='The-Gauntlet/'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,p in sorted(files):
            raw=p.read_bytes()
            archive.writestr(prefix+name,raw)
            manifest['files'][name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        archive.writestr(prefix+'PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None,'Archive CRC verification failed'
        for name,entry in manifest['files'].items():
            assert hashlib.sha256(archive.read(prefix+name)).hexdigest()==entry['sha256'],name
    checksum=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.sha256').write_text(checksum+'  '+output.name+'\n',encoding='utf-8')
    print(json.dumps({'path':str(output),'files':len(files),'MB':round(output.stat().st_size/1024/1024,1),'sha256':checksum,'verified':True}))


if __name__=='__main__':main()
