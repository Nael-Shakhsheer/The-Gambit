"""Prepare a public source manifest, excluding saves and large authoring art."""
import hashlib
import json
from pathlib import Path
from package_game import source_files


def main():
    root=Path(__file__).resolve().parents[1]
    text_entries=[]; binary_entries=[]
    for name,path in source_files(root,runtime_only=True):
        raw=path.read_bytes()
        sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if path.suffix.lower() in ('.png','.wav','.jpg','.jpeg','.zip'):
            binary_entries.append(dict(path=name,bytes=len(raw),sha=sha))
        else:
            text_entries.append(dict(path=name,mode='100644',type='blob',content=raw.decode('utf-8')))
    output=root/'releases'/'github-source-payload.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(dict(textTree=text_entries,binary=binary_entries),ensure_ascii=True),encoding='ascii')
    print(json.dumps(dict(payload=str(output),bytes=output.stat().st_size,textFiles=len(text_entries),binaryFiles=len(binary_entries))))


if __name__=='__main__':main()
