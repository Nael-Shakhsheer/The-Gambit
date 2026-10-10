"""Four HTTP clients exercise the real simulation in isolated combat fixtures.

This measures server reliability, not balance or physical-phone/Wi-Fi comfort.
No real rooms/checkpoints are read or written. --keep-open serves a browser QA
fixture until Ctrl+C; each browser uses its own localhost port identity.
"""
import argparse
import copy
import json
import logging
import math
from pathlib import Path
import statistics
import sys
import threading
import time
from unittest.mock import patch
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import game
import server


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--seconds', type=float, default=30)
    args.add_argument('--port', type=int, default=0)
    args.add_argument('--keep-open', action='store_true')
    args.add_argument('--report', type=Path)
    options = args.parse_args()
    world = game.GameWorld()
    server.WORLD = world
    code, host = world.create_room('Rogue QA')
    ids = [host]
    heroes = ['Rogue', 'Knight', 'Druid', 'Wizard']
    for hero in heroes[1:]:
        ids.append(world.join_room(code, hero+' QA')[1])
    for pid, hero in zip(ids, heroes):
        world.action(code, pid, {'action':'class', 'class':hero})
        world.action(code, pid, {'action':'loadout', 'abilities':[a[0] for a in game.ABILITY_SETS[hero][::2]]})
    world.action(code, host, {'action':'start'})
    room = world.rooms[code]
    room['story']['encountered'] = True
    errors, ticks = [], []
    class ErrorCapture(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR: errors.append(record.getMessage())
    capture = ErrorCapture(); logging.getLogger().addHandler(capture)
    original_tick = world.tick
    def timed_tick():
        start = time.perf_counter(); original_tick(); ticks.append(time.perf_counter()-start)
    world.tick = timed_tick
    class QAHandler(server.Handler):
        def _file(self, name, mime):
            if name == 'index.html' and options.keep_open:
                text = (server.STATIC/name).read_text(encoding='utf-8')
                session = json.dumps({'room':code, 'player':host})
                text = text.replace('<head>', '<head><script>localStorage.setItem("gauntlet-session",'+json.dumps(session)+');</script>')
                return self._send(200, text, mime)
            super()._file(name, mime)
    listener = server.ThreadingHTTPServer(('127.0.0.1', options.port), QAHandler)
    base = f'http://127.0.0.1:{listener.server_port}'
    stop = threading.Event()
    http = threading.Thread(target=listener.serve_forever, daemon=True); http.start()
    simulator = threading.Thread(target=server._simulation_loop, args=(stop,), daemon=True); simulator.start()
    start = time.monotonic(); responses = []; moves = [0]*4
    stages = [(7,'squadron'),(13,'regular'),(17,'regular'),(20,'boss'),(25,'dragon')]
    def request(path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        before = time.perf_counter()
        with urlopen(Request(base+path, data=data, headers={'Content-Type':'application/json'}), timeout=5) as response:
            result = json.load(response)
        responses.append(time.perf_counter()-before)
        return result
    def client(index):
        sequence, previous = 0, None
        try:
            while time.monotonic()-start < options.seconds:
                sequence += 1
                angle = sequence*.23+index*math.pi/2
                request('/api/action', {'room':code,'player':ids[index],'action':'input',
                        'sequence':sequence,'x':math.cos(angle),'y':math.sin(angle),'attack':True})
                view = request(f'/api/state?room={code}&player={ids[index]}')
                own = next(p for p in view['players'] if p['id'] == ids[index])
                position = (own['x'],own['y'])
                if previous and math.dist(previous,position) > .1: moves[index] += 1
                previous = position
                if sequence%15 == 0:
                    # Normal cooldown/mana rejection is expected, not a server fault.
                    try: request('/api/action', {'room':code,'player':ids[index],'action':'ability','slot':2})
                    except Exception as e:
                        if getattr(e,'code',None) != 400: raise
                stop.wait(.05)
        except Exception as e: errors.append(str(e))
        finally:
            try:
                world.action(code,ids[index],{'action':'input','sequence':sequence+1,'x':0,'y':0,'attack':False})
            except Exception as e: errors.append(str(e))
    workers = [threading.Thread(target=client,args=(i,),daemon=True) for i in range(4)]
    for worker in workers: worker.start()
    for index, (stage, kind) in enumerate(stages):
        with world.lock:
            room.update(stage=stage,phase='combat',stageWave=1,stageWaves=3,waveStartsAt=0,
                        hazards=[],projectiles=[],environment=None,objective=None,assassinationStage=None,
                        bossStages=[stage] if kind in ('boss','dragon') else [],miniBossStages=[])
            world._dismiss_summons(room)
            if kind == 'squadron':
                choose = lambda values: 'squadron' if 'empowered' in values else values[0]
                with patch('game.random.choice',side_effect=choose): world._spawn_mini_boss(room)
                world._tune_enemy_group(room)
            elif kind in ('boss','dragon'):
                room['bossSequence'] = [copy.deepcopy(game.LARGE_BOSSES[1]),copy.deepcopy(game.LARGE_BOSSES[2]),copy.deepcopy(game.DRAGON_TYPES[0])]
                room['bossesDefeated'] = 2 if kind == 'dragon' else 0
                room['stageWave'] = 3
                world._spawn_wave(room,preserve_players=True)
                if kind == 'dragon': world._damage_enemy(room,room['players'][host],room['enemies'][0],room['enemies'][0]['hp']+1)
            else: world._spawn_wave(room,preserve_players=True)
            for p in room['players'].values(): p.update(hp=5000,maxHp=5000,mana=1000,maxMana=1000)
            for enemy in room['enemies']: enemy.update(hp=5000,maxHp=5000)
            if kind == 'squadron':
                room['enemies'][0].update(hp=1,bleedUntil=time.monotonic()+3,bleedDamage=7,bleedOwner=host,lastBleedTick=0)
        stop.wait(max(0,start+(index+1)*options.seconds/len(stages)-time.monotonic()))
    for worker in workers: worker.join(timeout=6)
    health = request('/healthz')
    ordered = sorted(responses)
    report = {'clients':4,'seconds':options.seconds,'requests':len(responses),'simulationTicks':len(ticks),
              'movingSnapshotsPerClient':moves,'httpMedianMs':round(statistics.median(responses)*1000,2),
              'httpP95Ms':round(ordered[int(len(ordered)*.95)]*1000,2),
              'tickMaxMs':round(max(ticks)*1000,2),'errors':errors,'health':health,
              'fixtures':[{'stage':s,'kind':k} for s,k in stages],
              'note':'Synthetic localhost reliability fixtures with extra hero/enemy HP; not balance or physical-phone testing.'}
    if options.report:
        options.report.parent.mkdir(parents=True,exist_ok=True)
        options.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report),flush=True)
    assert not errors and all(moves) and health['ok'], 'Multiplayer reliability probe failed'
    if options.keep_open:
        print('Browser QA: '+base,flush=True)
        try:
            while True:
                with world.lock:
                    for p in room['players'].values(): p.update(status='alive',hp=p['maxHp'])
                time.sleep(1)
        except KeyboardInterrupt: pass
    stop.set(); listener.shutdown(); simulator.join(timeout=5); http.join(timeout=5)
    logging.getLogger().removeHandler(capture)


if __name__ == '__main__': main()
