import copy
import math
import unittest
from unittest.mock import patch

import boss_ai
import companion_ai
import combat_environment as terrain
import enemy_roles
import progression
import telemetry
from game import ABILITY_SETS, GameWorld


class CombatEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.
        timer = patch("game.time.monotonic",side_effect=lambda:self.now)
        timer.start(); self.addCleanup(timer.stop)
        self.world = GameWorld()
        self.code,self.pid = self.world.create_room("Hunter")
        self.world.action(self.code,self.pid,{"action":"class","class":"Knight"})
        self.world.action(self.code,self.pid,{"action":"loadout","abilities":[a[0] for a in ABILITY_SETS["Knight"][::2]]})
        self.world.action(self.code,self.pid,{"action":"start"})
        self.room = self.world.rooms[self.code]
        self.p = self.room["players"][self.pid]
        self.e = self.room["enemies"][0]
        self.room["enemies"] = [self.e]
        self.room["environment"] = {"stage":1,"region":self.room["region"],"obstacles":[],"zones":[]}
        self.p.update(x=100,y=100)
        self.e.update(x=500,y=100,hp=1000,maxHp=1000)

    def cover(self):
        o = {"id":"cover","kind":"crate","x":200,"y":100,"radius":24,"hp":24,"maxHp":24}
        self.room["environment"]["obstacles"] = [o]
        return o

    def test_environment_preserves_damage_between_waves_and_resets_per_stage(self):
        self.room["environment"] = None
        terrain.prepare(self.room)
        before = self.room["environment"]
        before["obstacles"][0]["hp"] = 0
        self.world._spawn_wave(self.room,preserve_players=True)
        self.assertIs(self.room["environment"],before)
        self.assertEqual(before["obstacles"][0]["hp"],0)
        self.room["stage"] += 1
        terrain.prepare(self.room)
        self.assertIsNot(self.room["environment"],before)
        self.assertTrue(all(o["hp"] == o["maxHp"] for o in terrain.obstacles(self.room)))

    def test_cover_blocks_walk_and_dash_without_tunnelling(self):
        o = self.cover()
        terrain.move(self.room,self.p,300,100)
        self.assertLess(self.p["x"],o["x"]-o["radius"]-11)
        self.p.update(x=100,y=100,dx=1,dy=0)
        self.world.action(self.code,self.pid,{"action":"dash"})
        self.assertLess(self.p["x"],165)

    def test_cover_absorbs_enemy_shot_and_destroying_it_opens_path(self):
        o=self.cover(); self.p.update(x=300,y=100)
        self.world._launch_projectile(self.room,side="enemy",owner_id=self.e["id"],target_id=self.pid,
            x=100,y=100,damage=24,color="#fff",attack_class="Archer",speed=1000,turn_rate=0)
        self.now+=.12; self.world._tick_projectiles(self.room,self.now)
        self.assertEqual(o["hp"],0)
        self.assertEqual(self.p["hp"],self.p["maxHp"])
        self.assertFalse(self.room["projectiles"])
        terrain.move(self.room,self.p,100,100)
        self.assertEqual(self.p["x"],100)

    def test_first_target_in_front_of_cover_is_hit_before_cover(self):
        o=self.cover(); self.e.update(x=145,y=100)
        self.world._launch_projectile(self.room,side="hero",owner_id=self.pid,target_id=self.e["id"],
            x=100,y=100,damage=10,color="#fff",attack_class="Archer",speed=1000)
        self.now+=.12; self.world._tick_projectiles(self.room,self.now)
        self.assertEqual(self.e["hp"],990)
        self.assertEqual(o["hp"],24)

    def test_light_attacks_destroy_cover_without_awarding_combat_damage(self):
        o=self.cover()
        for _ in range(3):
            self.world._attack(self.room,self.p); self.now+=.5
        self.assertEqual(o["hp"],0)
        self.assertEqual(telemetry.overall(self.room)[0]["damageDealt"],0)

    def test_trap_warns_then_allows_escape_and_rearms(self):
        z={"kind":"trap","x":100,"y":100,"radius":34,"warnAt":0,"readyAt":0}
        self.room["environment"]["zones"]=[z]
        hp=self.p["hp"]
        terrain.tick(self.world,self.room,self.now)
        self.assertEqual(self.p["hp"],hp)
        self.assertEqual(z["warnAt"],self.now+.75)
        self.p["x"]=160; self.now+=.8
        terrain.tick(self.world,self.room,self.now)
        self.assertEqual(self.p["hp"],hp)
        self.p["x"]=100; self.now+=4.1
        terrain.tick(self.world,self.room,self.now)
        self.now+=.8;terrain.tick(self.world,self.room,self.now)
        self.assertLess(self.p["hp"],hp)

    def test_poison_ticks_once_per_second_and_ignores_downed_heroes(self):
        self.room["environment"]["zones"]=[{"kind":"poison","x":100,"y":100,"radius":48}]
        hp=self.p["hp"]
        terrain.tick(self.world,self.room,self.now)
        terrain.tick(self.world,self.room,self.now+.2)
        self.assertEqual(self.p["hp"],hp-3)
        self.p.update(status="downed",hp=0)
        terrain.tick(self.world,self.room,self.now+2)
        self.assertEqual(self.p["hp"],0)

    def test_ice_carries_momentum_after_releasing_movement(self):
        self.room["environment"]["zones"]=[{"kind":"ice","x":100,"y":100,"radius":105}]
        terrain.player_move(self.room,self.p,1,0,140,.1)
        before=self.p["x"]
        terrain.player_move(self.room,self.p,0,0,140,.1)
        self.assertGreater(self.p["x"],before)
        self.room["environment"]["zones"]=[]
        before=self.p["x"]
        terrain.player_move(self.room,self.p,0,0,140,.1)
        self.assertEqual(self.p["x"],before)

    def test_role_assignment_has_support_and_assassins_remain_ambushers(self):
        self.room["enemies"]=[dict(self.e,id=str(i),kind=k) for i,k in enumerate(("minotaur","serpent","troll"))]
        enemy_roles.assign(self.room)
        self.assertEqual([e["combatRole"] for e in self.room["enemies"]],["charger","ranged","support"])
        self.room["enemies"][-1]["assassin"]=True
        enemy_roles.assign(self.room)
        self.assertEqual(self.room["enemies"][-1]["combatRole"],"ambusher")

    def test_support_heals_one_surviving_ally_after_windup_and_does_not_overheal(self):
        self.e.update(combatRole="support",x=100,y=100)
        ally=dict(self.e,id="ally",x=120,y=100,hp=99,maxHp=100)
        self.room["enemies"].append(ally)
        self.e["roleAttack"]={"kind":"support","x":100,"y":100,"targetId":self.pid,"ally":"ally","startedAt":self.now,"releaseAt":self.now+.8}
        enemy_roles.tick(self.world,self.room,self.e,self.p,self.now,.05)
        self.assertEqual(ally["hp"],99)
        self.now+=.81
        enemy_roles.tick(self.world,self.room,self.e,self.p,self.now,.05)
        self.assertEqual(ally["hp"],100)
        self.assertGreater(self.e["roleRecoverUntil"],self.now)

    def test_enemy_cancels_windup_when_target_is_downed(self):
        other=dict(self.p,id="other",x=500,y=250)
        self.room["players"]["other"]=other
        self.e.update(targetId=self.pid,combatRole="ranged",roleAttack={"kind":"ranged","x":100,"y":100,"targetId":self.pid,"startedAt":self.now,"releaseAt":self.now+1})
        self.p.update(status="downed",hp=0)
        self.world._tick_enemy(self.room,self.e,other,self.now)
        self.assertNotIn("roleAttack",self.e)
        self.assertEqual(self.e["targetId"],"other")

    def test_boss_release_is_followed_by_stationary_recovery(self):
        self.e.update(kind="troll",boss=True,attackIndex=1,nextBossAttack=0)
        boss_ai.tick(self.world,self.room,self.e,self.p,self.now,.05)
        self.assertFalse(self.room["projectiles"])
        release=self.e["pendingAttack"]["releaseAt"]
        boss_ai.tick(self.world,self.room,self.e,self.p,release-.01,.05)
        self.assertFalse(self.room["projectiles"])
        boss_ai.tick(self.world,self.room,self.e,self.p,release+.01,.05)
        self.assertEqual(len(self.room["projectiles"]),3)
        before=(self.e["x"],self.e["y"])
        boss_ai.tick(self.world,self.room,self.e,self.p,release+.5,.05)
        self.assertEqual((self.e["x"],self.e["y"]),before)

    def test_repeat_stuns_cannot_permanently_lock_an_enemy(self):
        self.world._stun(self.e,self.now)
        first=self.e["stunUntil"]
        self.world._stun(self.e,self.now+.45)
        self.assertEqual(self.e["stunUntil"],first)
        self.assertLess(first,self.now+1.8)
        self.world._stun(self.e,self.now+1.81)
        self.assertGreater(self.e["stunUntil"],first)

    def test_companion_dodges_projectile_then_changes_side_and_keeps_attacking(self):
        bot=self.p
        self.e.update(x=300,y=100,combatRole="ranged")
        self.world._launch_projectile(self.room,side="enemy",owner_id=self.e["id"],target_id=self.pid,
            x=220,y=100,damage=10,color="#fff",attack_class="Archer",speed=225,turn_rate=0)
        bot["attacking"]=True
        self.assertTrue(companion_ai.defensive_move(self.room,bot,self.e,240,self.now))
        first=bot["aiDodgeSide"]
        self.assertNotEqual(bot["dy"],0)
        self.assertTrue(bot["attacking"])
        self.assertTrue(terrain.walkable(self.room,*bot["aiDodgeGoal"]))
        self.now+=2
        self.assertTrue(companion_ai.defensive_move(self.room,bot,self.e,240,self.now))
        self.assertEqual(bot["aiDodgeSide"],-first)

    def test_actual_healing_is_single_target_and_wards_credit_the_caster(self):
        healer=self.p
        healer.update(**{"class":"Healer"},abilities=["life_spark","major_mend","miracle"],hp=90,maxHp=110)
        ally=dict(healer,id="ally",hp=10,maxHp=110,x=120,y=100)
        self.room["players"]["ally"]=ally
        telemetry.start(self.room,self.now,ABILITY_SETS)
        self.world._cast_ability(self.room,healer,1)
        self.assertEqual(healer["hp"],90)
        self.assertEqual(ally["hp"],65)
        self.assertEqual(self.room["combatStats"]["players"][self.pid]["healingGiven"],55)
        ally.update(wardUntil=self.now+8,wardFactor=.5,wardSource=self.pid)
        self.world._damage_player(self.room,self.e,ally,20)
        self.assertEqual(self.room["combatStats"]["players"][self.pid]["protectionGiven"],10)
        self.assertEqual(set(telemetry.overall(self.room)[0])-{ "name","class" },{"damageDealt","damageTaken","kills","deaths","revives"})

    def test_clock_pause_includes_terrain_dodge_and_recovery(self):
        clocks={key:self.now+1 for key in ("warnAt","readyAt","terrainHitAt","roleReadyAt","roleRecoverUntil","recoverUntil","stunResistUntil","aiDodgeUntil")}
        self.world._shift_clocks(clocks,20)
        self.assertTrue(all(t==self.now+21 for t in clocks.values()))

    def test_summons_lose_temporary_damage_boost_when_it_expires(self):
        self.p.update(**{"class":"Druid"},abilities=["thornshot","fire_wolf","ice_bear"],damageBoost=1.5,damageBoostUntil=self.now+1)
        self.world._cast_ability(self.room,self.p,1)
        wolf=self.room["summons"][0]
        boosted=wolf["damage"]
        self.e.update(x=wolf["x"]+10,y=wolf["y"])
        self.now+=1.2
        self.world._tick_summons(self.room,self.now)
        self.assertEqual(wolf["damage"],12)  # Thornshot: round(12*1.05)=13; wolf: round(13*.9)=12.
        self.assertLess(wolf["damage"],boosted)

    def test_projectile_boost_credit_survives_buff_expiration_without_double_counting(self):
        self.p.update(**{"class":"Wizard"},damageBoost=1.5,damageBoostUntil=self.now+.1,damageBoostSource=self.pid)
        self.e.update(x=160,y=100)
        self.world._launch_projectile(self.room,side="hero",owner_id=self.pid,target_id=self.e["id"],
            x=100,y=100,damage=15,color="#fff",attack_class="Wizard",speed=400)
        self.now+=.12;self.world._tick_projectiles(self.room,self.now)
        row=self.room["combatStats"]["players"][self.pid]
        self.assertEqual(row["boostDamageGiven"],5)
        self.assertEqual(row["heroDamage"],15)

    def test_companion_escape_goal_respects_cover(self):
        self.cover();self.e.update(x=220,y=100)
        self.room["hazards"]=[{"x":100,"y":100,"radius":70}]
        self.assertTrue(companion_ai.defensive_move(self.room,self.p,self.e,240,self.now))
        goal=self.p["aiDodgeGoal"]
        self.assertTrue(terrain.line_clear(self.room,self.p,{"x":goal[0],"y":goal[1]}))
        self.assertGreater(math.hypot(goal[0]-100,goal[1]-100),70)

    def test_each_dialogue_has_player_reply_and_correct_npc(self):
        for kind,(title,pages) in progression.PAGES.items():
            progression.start_dialogue(self.p,kind)
            for page in range(len(pages)):
                self.p["dialogue"]["page"]=page
                d=progression.dialogue(self.p)
                self.assertEqual(d["title"],title)
                self.assertTrue(d["reply"])
                self.assertEqual(d["text"],pages[page])


if __name__ == "__main__": unittest.main()
