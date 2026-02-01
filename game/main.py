import arcade
import random
import math
import csv
from pathlib import Path
from arcade import Text
import time


SW = 1000
SH = 700
SCT = "Космический Шутер"

PSP = 2
PH = 100
PFR = 0.15

ESP = 2
ESI = 2.0

BSP = 10
EBSP = 5

LVL1SC = 500
LVL2SC = 1500
LVL3SC = 3000
LVL4SC = 5000

CLB = arcade.color.BLACK
CLUI = arcade.color.WHITE
CHF = arcade.color.GREEN
CHL = arcade.color.RED


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.color = color
        self.alpha = 255
        self.size = random.randint(2, 5)
        self.lifetime = random.uniform(0.5, 1.5)
        self.age = 0

    def update(self, delta_time):
        self.x += self.vx
        self.y += self.vy
        self.age += delta_time
        self.alpha = int(255 * (1 - self.age / self.lifetime))
        return self.age < self.lifetime

    def draw(self):
        if self.alpha > 0:
            arcade.draw_circle_filled(
                self.x, self.y, self.size,
                self.color if isinstance(self.color, tuple) else arcade.color.WHITE
            )


class ParticleSystem:
    def __init__(self):
        self.prs = []

    def create_explosion(self, x, y, color, count=20):
        for _ in range(count):
            self.prs.append(Particle(x, y, color))

    def update(self, delta_time):
        self.prs = [p for p in self.prs if p.update(delta_time)]

    def draw(self):
        for pr in self.prs:
            pr.draw()


class Player(arcade.Sprite):
    def __init__(self, textures=None):
        super().__init__()
        self.width = 40
        self.height = 50
        self.health = PH
        self.score = 5000
        self.fire_timer = 0
        self.level = 1
        self.can_shoot = True
        self.text = textures or []
        self.skid = 0
        if self.text:
            self.texture = self.text[self.skid]
        else:
            self.texture = arcade.make_soft_square_texture(
                self.width, arcade.color.CYAN, outer_alpha=255
            )

    def apply_skin(self, index: int):
        if self.text:
            self.skid = index % len(self.text)
            self.texture = self.text[self.skid]

    def cycle_skin(self):
        if self.text:
            self.skid = (self.skid + 1) % len(self.text)
            self.texture = self.text[self.skid]

    def update(self):
        super().update()
        self.center_x += self.change_x
        self.center_y += self.change_y
        if self.left < 0:
            self.left = 0
        elif self.right > SW:
            self.right = SW
        if self.bottom < 0:
            self.bottom = 0
        elif self.top > SH:
            self.top = SH

    def update_fire_timer(self, delta_time):
        if not self.can_shoot:
            self.fire_timer += delta_time
            if self.fire_timer >= PFR:
                self.can_shoot = True
                self.fire_timer = 0

    def take_damage(self, damage):
        self.health = max(0, self.health - damage)
        return self.health <= 0


class Enemy(arcade.Sprite):
    def __init__(self, enemy_type, level, texture=None):
        super().__init__()
        self.enemy_type = enemy_type
        self.w = 45
        self.h = 45
        bshp = 20 + (level * 10)
        if enemy_type == 'fast':
            self.max_health = int(bshp * 0.7)
            self.spm = 1.5
            self.damage = 10
            color = arcade.color.ORANGE

        elif enemy_type == 'tank':
            self.max_health = int(bshp * 1.8)
            self.spm = 0.7
            self.damage = 25
            color = arcade.color.PURPLE

        else:
            self.max_health = bshp
            self.spm = 1.0
            self.damage = 15
            color = arcade.color.RED

        self.health = self.max_health
        self.sht = 0
        self.shit = random.uniform(1.5, 3.0)
        if texture is not None:
            self.texture = texture
        else:
            self.texture = arcade.make_soft_circle_texture(
                self.w, color, outer_alpha=255
            )

    def update(self):
        super().update()
        self.center_y -= ESP * self.spm
        self.center_x += math.sin(self.center_y / 50) * 2

    def update_shoot_timer(self, delta_time):
        self.sht += delta_time
        if self.sht >= self.shit:
            self.sht = 0
            return True
        return False

    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0

    def draw_health_bar(self):
        if self.health <= 0:
            return

        bww = 40
        bhh = 5
        hltr = self.health / self.max_health

        if hltr > 0.5:
            color = arcade.color.GREEN
        elif hltr > 0.25:
            color = arcade.color.YELLOW
        else:
            color = arcade.color.RED

        arcade.draw_lrbt_rectangle_filled(
            self.center_x - bww / 2,
            self.center_x + bww / 2,
            self.top + 8,
            self.top + 8 + bhh,
            arcade.color.DARK_RED
        )

        arcade.draw_lrbt_rectangle_filled(
            self.center_x - bww / 2,
            self.center_x - bww / 2 + bww * hltr,
            self.top + 8,
            self.top + 8 + bhh,
            color
        )


class Boss(arcade.Sprite):
    def __init__(self, textures=None):
        super().__init__()

        self.width = 160
        self.height = 120

        self.max_health = 1500
        self.health = self.max_health

        self.phase = 1
        self.damage = 30

        self.shoot_timer = 0

        self.textures = textures or []

        if self.textures:
            self.texture = self.textures[0]
        else:
            self.texture = arcade.make_soft_square_texture(
                max(self.width, self.height), arcade.color.DARK_RED, outer_alpha=255
            )

    def update(self):
        self.center_x += math.sin(time.time() * 1.5) * 2
        hp_ratio = self.health / self.max_health
        old_phase = self.phase
        if hp_ratio <= 0.33:
            self.phase = 3
        elif hp_ratio <= 0.66:
            self.phase = 2
        else:
            self.phase = 1
        if self.textures and old_phase != self.phase:
            idx = max(0, min(2, self.phase - 1))
            self.texture = self.textures[idx]

    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0


class Bullet(arcade.Sprite):
    def __init__(self, x, y, damage, is_player_bullet=True):
        super().__init__()
        self.width = 12
        self.height = 30
        self.is_player_bullet = is_player_bullet
        self.damage = damage
        color = arcade.color.YELLOW if is_player_bullet else arcade.color.RED_ORANGE
        self.texture = arcade.make_soft_square_texture(
            max(self.width, self.height), color, outer_alpha=255
        )
        self.center_x = x
        self.center_y = y
        self.change_y = BSP if is_player_bullet else -EBSP


class PowerUp(arcade.Sprite):
    def __init__(self, x, y, powerup_type, texture=None):
        super().__init__()
        self.powerup_type = powerup_type
        self.width = 30
        self.height = 30
        if texture is not None:
            self.texture = texture
        else:
            colors = {
                'health': arcade.color.GREEN,
                'speed': arcade.color.BLUE,
                'damage': arcade.color.ORANGE
            }
            color = colors.get(powerup_type, arcade.color.WHITE)
            self.texture = arcade.make_soft_circle_texture(
                self.width, color, outer_alpha=200
            )
        self.center_x = x
        self.center_y = y
        self.change_y = -2


class StarField:
    def __init__(self, star_count=100):
        self.sts = []
        for _ in range(star_count):
            x = random.randint(0, SW)
            y = random.randint(0, SH)
            sped = random.uniform(0.5, 2)
            szz = random.randint(1, 3)
            self.sts.append({'x': x, 'y': y, 'speed': sped, 'size': szz})

    def update(self):
        for st in self.sts:
            st['y'] -= st['speed']
            if st['y'] < 0:
                st['y'] = SH
                st['x'] = random.randint(0, SW)

    def draw(self):
        for st in self.sts:
            arcade.draw_circle_filled(
                st['x'], st['y'], st['size'],
                arcade.color.WHITE
            )


class Camera:
    def __init__(self):
        self.shofx = 0
        self.shofy = 0
        self.si = 0
        self.sd = 0

    def shake(self, intensity=10, duration=0.3):
        self.si = intensity
        self.sd = duration

    def update(self, delta_time):
        if self.sd > 0:
            self.sd -= delta_time
            self.shofx = random.uniform(-self.si, self.si)
            self.shofy = random.uniform(-self.si, self.si)
        else:
            self.shofx = 0
            self.shofy = 0


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.ply = None
        self.enel = None
        self.bulll = None
        self.pwupll = None
        self.partil = None
        self.stll = None
        self.camera = None
        self.est = 0
        self.pstr = 0
        self.game_over = False
        self.paused = False
        self.curlvl = 1
        self.boss = None
        self.bsffgg = False
        self.bosslst = arcade.SpriteList()
        self.victory = False
        self.setup_sounds()
        arcade.set_background_color(CLB)
        self.pltest = []
        self.entetx = []
        self.boss_textures = []
        self.pwupt = {}

    def setup_sounds(self):
        pass

    def load_texture_safe(self, path: Path, fallback_callable):
        try:
            if path.exists():
                return arcade.load_texture(str(path))
        except Exception:
            pass
        return fallback_callable()

    def setup(self):
        assets_dir = Path(__file__).parent / "assets"
        pff = [assets_dir / f"player_skin{i}.png" for i in (1, 2, 3)]
        def player_fallback(i=0):
            return arcade.make_soft_square_texture(40, arcade.color.CYAN, outer_alpha=255)
        self.pltest = [self.load_texture_safe(p, player_fallback) for p in pff]
        enf = [assets_dir / f"enemy_skin{i}.png" for i in (1, 2, 3)]
        def enemy_fallback(i=0):
            return arcade.make_soft_circle_texture(45, arcade.color.RED, outer_alpha=255)
        self.entetx = [self.load_texture_safe(p, enemy_fallback) for p in enf]
        bsf = [assets_dir / f"boss_phase{i}.png" for i in (1, 2, 3)]
        def boss_fallback(i=0):
            return arcade.make_soft_square_texture(160, arcade.color.DARK_RED, outer_alpha=255)
        self.boss_textures = [self.load_texture_safe(p, boss_fallback) for p in bsf]
        pwupmp = {
            'health': assets_dir / 'powerup_health.png',
            'speed': assets_dir / 'powerup_speed.png',
            'damage': assets_dir / 'powerup_damage.png'
        }

        def powerup_fallback_health():
            return arcade.make_soft_circle_texture(30, arcade.color.GREEN, outer_alpha=200)

        def powerup_fallback_speed():
            return arcade.make_soft_circle_texture(30, arcade.color.BLUE, outer_alpha=200)

        def powerup_fallback_damage():
            return arcade.make_soft_circle_texture(30, arcade.color.ORANGE, outer_alpha=200)

        self.pwupt = {
            'health': self.load_texture_safe(pwupmp['health'], powerup_fallback_health),
            'speed': self.load_texture_safe(pwupmp['speed'], powerup_fallback_speed),
            'damage': self.load_texture_safe(pwupmp['damage'], powerup_fallback_damage),
        }

        self.ply = Player(textures=self.pltest)
        self.ply.center_x = SW // 2
        self.ply.center_y = 100
        self.plrl = arcade.SpriteList()
        self.plrl.append(self.ply)
        self.enel = arcade.SpriteList()
        self.bulll = arcade.SpriteList()
        self.pwupll = arcade.SpriteList()
        self.partil = ParticleSystem()
        self.stll = StarField(150)
        self.cmsp = arcade.camera.Camera2D()
        self.shh = Camera()
        self.est = 0
        self.pstr = 0
        self.game_over = False
        self.paused = False
        self.curlvl = 1
        self.health_text = Text(
            f"HP: {self.ply.health}",
            10, SH - 20,
            arcade.color.GREEN, 18, bold=True
        )
        self.score_text = Text(
            f"Счёт: {self.ply.score}",
            10, SH - 60,
            CLUI, 18, bold=True
        )
        self.level_text = Text(
            f"Уровень: {self.curlvl}",
            10, SH - 90,
            CLUI, 18, bold=True
        )
        self.controls_text = Text(
            "WASD - движение | SPACE - стрельба | P - пауза | C - смена скина игрока",
            SW // 2, 20,
            CLUI, 12,
            anchor_x="center"
        )
        self.game_over_title = Text(
            "ИГРА ОКОНЧЕНА",
            SW // 2, SH // 2 + 80,
            arcade.color.RED, 36, bold=True,
            anchor_x="center"
        )
        self.game_over_score = Text(
            "",
            SW // 2, SH // 2 + 20,
            CLUI, 24,
            anchor_x="center"
        )
        self.game_over_level = Text(
            "",
            SW // 2, SH // 2 - 20,
            CLUI, 20,
            anchor_x="center"
        )
        self.game_over_hint = Text(
            "Нажмите ENTER для возврата в меню",
            SW // 2, SH // 2 - 80,
            CLUI, 16,
            anchor_x="center"
        )
        self.pause_title = Text(
            "ПАУЗА",
            SW // 2, SH // 2 + 20,
            CLUI, 32, bold=True,
            anchor_x="center"
        )
        self.pause_hint = Text(
            "Нажмите P для продолжения",
            SW // 2, SH // 2 - 30,
            CLUI, 16,
            anchor_x="center"
        )

    def spawn_enemy(self):
        ent = ['basic', 'fast', 'tank']
        ww = [0.6, 0.25, 0.15]
        entt = random.choices(ent, weights=ww)[0]
        tex = None
        if self.entetx:
            tex = random.choice(self.entetx)
        enemy = Enemy(entt, self.curlvl, texture=tex)
        enemy.center_x = random.randint(50, SW - 50)
        enemy.center_y = SH + 30
        self.enel.append(enemy)

    def start_boss_fight(self):
        self.enel.clear()
        self.bulll.clear()
        self.pwupll.clear()
        self.est = 0
        self.pstr = 0
        self.boss = Boss(textures=self.boss_textures)
        self.boss.center_x = SW // 2
        self.boss.center_y = SH - 120
        self.bosslst.clear()
        self.bosslst.append(self.boss)
        self.bsffgg = True
        self.victory = False

    def spawn_powerup(self):
        powerup_types = ['health', 'speed', 'damage']
        powerup_type = random.choice(powerup_types)
        tex = self.pwupt.get(powerup_type)
        pwup = PowerUp(
            random.randint(50, SW - 50),
            SH + 30,
            powerup_type,
            texture=tex
        )
        self.pwupll.append(pwup)

    def update_level(self):
        oldl = self.curlvl

        if self.ply.score >= LVL4SC:
            self.curlvl = 4
        elif self.ply.score >= LVL3SC:
            self.curlvl = 3
        elif self.ply.score >= LVL2SC:
            self.curlvl = 2
        elif self.ply.score >= LVL1SC:
            self.curlvl = 1

        if oldl != self.curlvl:
            self.partil.create_explosion(
                SW // 2,
                SH // 2,
                arcade.color.GOLD,
                80
            )
            if self.curlvl == 4:
                self.start_boss_fight()

    def on_update(self, delta_time):
        if self.game_over or self.paused:
            return
        self.stll.update()
        self.shh.update(delta_time)
        self.ply.update()
        self.ply.update_fire_timer(delta_time)
        self.update_level()

        if self.bsffgg and self.boss:
            self.boss.update()
            self.boss.sht += delta_time
            if self.boss.phase == 1 and self.boss.sht > 1.0:
                for ang in [-45, -30, -15, 0, 15, 30, 45]:
                    bl = Bullet(
                        self.boss.center_x,
                        self.boss.bottom,
                        damage=35,
                        is_player_bullet=False
                    )
                    bl.chx = math.sin(math.radians(ang)) * 6
                    bl.chy = -BSP
                    self.bulll.append(bl)
                self.boss.sht = 0

            elif self.boss.phase == 2 and self.boss.sht > 0.8:
                for ang in range(0, 360, 20):
                    bl = Bullet(
                        self.boss.center_x,
                        self.boss.center_y,
                        damage=40,
                        is_player_bullet=False
                    )
                    bl.chx = math.cos(math.radians(ang)) * 6
                    bl.chy = math.sin(math.radians(ang)) * 6
                    self.bulll.append(bl)
                self.boss.sht = 0

            elif self.boss.phase == 3 and self.boss.sht > 0.5:
                for _ in range(12):
                    bl = Bullet(
                        random.randint(100, SW - 100),
                        self.boss.bottom,
                        damage=50,
                        is_player_bullet=False
                    )
                    bl.chy = -10
                    bl.chx = random.uniform(-3, 3)
                    self.bulll.append(bl)
                self.boss.sht = 0

        self.enel.update()
        for en in self.enel:
            if en.update_shoot_timer(delta_time):
                bl = Bullet(
                    en.center_x,
                    en.center_y,
                    damage=en.damage,
                    is_player_bullet=False
                )
                self.bulll.append(bl)

        self.bulll.update()
        self.pwupll.update()
        self.partil.update(delta_time)

        if not self.bsffgg:
            self.est += delta_time
            spi = max(0.8, ESI - self.curlvl * 0.2)
            if self.est >= spi:
                self.spawn_enemy()
                self.est = 0

        self.pstr += delta_time
        if self.pstr >= 10:
            self.spawn_powerup()
            self.pstr = 0

        for bl in list(self.bulll):
            if bl.is_player_bullet:
                he = arcade.check_for_collision_with_list(bl, self.enel)
                if self.bsffgg and self.boss:
                    if arcade.check_for_collision(bl, self.boss):
                        if self.boss.take_damage(bl.damage):
                            self.partil.create_explosion(
                                self.boss.center_x,
                                self.boss.center_y,
                                arcade.color.GOLD,
                                200
                            )
                            self.ply.score += 5000
                            self.bosslst.clear()
                            self.boss = None
                            self.bsffgg = False
                            self.victory = True
                            self.game_over = True
                            self.save_score()
                        bl.remove_from_sprite_lists()
                        break
                if he:
                    for en in he:
                        if en.take_damage(bl.damage):
                            self.partil.create_explosion(en.center_x, en.center_y, arcade.color.ORANGE)
                            en.remove_from_sprite_lists()
                            self.ply.score += 50
                    bl.remove_from_sprite_lists()
                    break

        for bl in list(self.bulll):
            if not bl.is_player_bullet:
                if arcade.check_for_collision(bl, self.ply):
                    if self.ply.take_damage(bl.damage):
                        self.game_over = True
                        self.save_score()
                    bl.remove_from_sprite_lists()
                    self.shh.shake(8, 0.3)

        he = arcade.check_for_collision_with_list(self.ply, self.enel)
        for en in he:
            if self.ply.take_damage(en.damage):
                self.game_over = True
                self.save_score()

            en.remove_from_sprite_lists()
            self.partil.create_explosion(
                en.center_x, en.center_y,
                arcade.color.RED, 20
            )
            self.shh.shake(10, 0.4)

        hpt = arcade.check_for_collision_with_list(self.ply, self.pwupll)
        for pwr in hpt:
            if pwr.powerup_type == 'health':
                self.ply.health = min(PH, self.ply.health + 30)
            pwr.remove_from_sprite_lists()

        for en in list(self.enel):
            if en.top < 0:
                en.remove_from_sprite_lists()
        for bl in list(self.bulll):
            if bl.bottom > SH or bl.top < 0:
                bl.remove_from_sprite_lists()
        for pwr in list(self.pwupll):
            if pwr.top < 0:
                pwr.remove_from_sprite_lists()

        self.update_level()

    def on_draw(self):
        self.clear()

        cam_x = SW // 2 + self.shh.shofx
        cam_y = SH // 2 + self.shh.shofy
        self.cmsp.position = (cam_x, cam_y)

        with self.cmsp.activate():
            self.stll.draw()
            self.bulll.draw()
            self.enel.draw()
            if self.bsffgg:
                self.bosslst.draw()

            for en in self.enel:
                en.draw_health_bar()

            self.pwupll.draw()
            self.plrl.draw()
            self.partil.draw()

        self.draw_ui()

        if self.game_over:
            self.draw_game_over()

        if self.paused:
            self.draw_pause()

    def draw_ui(self):
        hpr = self.ply.health / PH
        hc = CHF if hpr > 0.3 else CHL

        self.health_text.text = f"HP: {self.ply.health}"
        self.health_text.color = hc
        self.health_text.draw()

        bw = max(0, 200 * hpr)
        arcade.draw_lrbt_rectangle_filled(
            0, bw, SH - 39, SH - 24,
            hc
        )
        arcade.draw_lrbt_rectangle_outline(
            0, 200, SH - 39, SH - 24,
            CLUI, 2
        )

        self.score_text.text = f"Счёт: {self.ply.score}"
        self.score_text.draw()

        self.level_text.text = f"Уровень: {self.curlvl}"
        self.level_text.draw()

        self.controls_text.draw()

        if self.bsffgg and self.boss is not None:
            bw = 600
            bh = 20
            cx = SW // 2
            cy = SH - 50

            arcade.draw_lrbt_rectangle_filled(
                left=cx - bw / 2,
                right=cx + bw / 2,
                bottom=cy - bh / 2,
                top=cy + bh / 2,
                color=arcade.color.BLACK
            )

            hr = max(0, self.boss.health / self.boss.max_health)
            cw = bw * hr

            if cw > 0:
                arcade.draw_lrbt_rectangle_filled(
                    left=cx - bw / 2,
                    right=cx - bw / 2 + cw,
                    bottom=cy - bh / 2,
                    top=cy + bh / 2,
                    color=arcade.color.RED
                )

            arcade.draw_lrbt_rectangle_outline(
                left=cx - bw / 2,
                right=cx + bw / 2,
                bottom=cy - bh / 2,
                top=cy + bh / 2,
                color=arcade.color.WHITE,
                border_width=2
            )

            arcade.draw_text("ФИНАЛЬНЫЙ БОСС", cx, cy + 20, arcade.color.WHITE, 12, anchor_x="center")

    def draw_game_over(self):
        arcade.draw_lrbt_rectangle_filled(
            SW // 2 - 200, SW // 2 + 200,
            SH // 2 - 150, SH // 2 + 150,
            CLB.replace(a=230)
        )
        if getattr(self, "victory", False):
            tt = "ПОБЕДА!"
            tc = arcade.color.GOLD
        else:
            tt = "ИГРА ОКОНЧЕНА"
            tc = arcade.color.RED
        arcade.draw_text(tt,
                         SW // 2, SH // 2 + 80,
                         tc, 36, bold=True, anchor_x="center")
        self.game_over_score.text = f"Ваш счёт: {self.ply.score}"
        self.game_over_level.text = f"Достигнутый уровень: {self.curlvl}"
        self.game_over_score.draw()
        self.game_over_level.draw()
        self.game_over_hint.draw()

    def draw_pause(self):
        arcade.draw_lrbt_rectangle_filled(
            SW // 2 - 150, SW // 2 + 150,
            SH // 2 - 75, SH // 2 + 75,
            CLB.replace(a=200)
        )
        self.pause_title.draw()
        self.pause_hint.draw()

    def on_key_press(self, key, modifiers):
        if self.game_over:
            if key == arcade.key.ENTER:
                menu_view = MenuView()
                self.window.show_view(menu_view)
            return
        if key == arcade.key.P:
            self.paused = not self.paused
            return
        if self.paused:
            return
        if key == arcade.key.W:
            self.ply.chy = PSP
        elif key == arcade.key.S:
            self.ply.chy = -PSP
        elif key == arcade.key.A:
            self.ply.chx = -PSP
        elif key == arcade.key.D:
            self.ply.chx = PSP
        elif key == arcade.key.SPACE:
            if self.ply.can_shoot:
                bullet = Bullet(
                    self.ply.center_x,
                    self.ply.top,
                    damage=20,
                    is_player_bullet=True
                )
                self.bulll.append(bullet)
                self.ply.can_shoot = False
        elif key == arcade.key.C:
            self.ply.cycle_skin()

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.W, arcade.key.S):
            self.ply.chy = 0
        elif key in (arcade.key.A, arcade.key.D):
            self.ply.chx = 0

    def save_score(self):
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)
        scores_file = data_dir / "scores.csv"
        scores = []
        if scores_file.exists():
            with open(scores_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)
                scores = list(reader)
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scores.append([timestamp, str(self.ply.score), str(self.curlvl)])
        scores.sort(key=lambda x: int(x[1]), reverse=True)
        with open(scores_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Дата', 'Счёт', 'Уровень'])
            writer.writerows(scores[:10])


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.star_field = StarField(100)
        self.title_text = Text(
            "КОСМИЧЕСКИЙ ШУТЕР",
            SW // 2, SH - 150,
            arcade.color.CYAN, 48, bold=True,
            anchor_x="center"
        )
        self.start_text = Text(
            "Нажмите ENTER для начала игры",
            SW // 2, SH // 2,
            CLUI, 24,
            anchor_x="center"
        )
        self.highscore_text = Text(
            "Нажмите H для просмотра рекордов",
            SW // 2, SH // 2 - 50,
            CLUI, 20,
            anchor_x="center"
        )
        self.controls_text = Text(
            "Управление: WASD - движение, SPACE - стрельба",
            SW // 2, SH // 2 - 120,
            arcade.color.LIGHT_GRAY, 16,
            anchor_x="center"
        )
        self.goal_text = Text(
            "Цель: уничтожайте врагов и набирайте очки!",
            SW // 2, SH // 2 - 160,
            arcade.color.LIGHT_GRAY, 16,
            anchor_x="center"
        )

    def on_show_view(self):
        arcade.set_background_color(CLB)

    def on_update(self, delta_time):
        self.star_field.update()

    def on_draw(self):
        self.clear()
        self.star_field.draw()
        self.title_text.draw()
        self.start_text.draw()
        self.highscore_text.draw()
        self.controls_text.draw()
        self.goal_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            game_view = GameView()
            game_view.setup()
            self.window.show_view(game_view)
        elif key == arcade.key.H:
            highscore_view = HighScoreView()
            self.window.show_view(highscore_view)


class HighScoreView(arcade.View):
    def __init__(self):
        super().__init__()
        self.star_field = StarField(100)
        self.scores = []
        self.load_scores()
        self.title_text = Text(
            "ТАБЛИЦА РЕКОРДОВ",
            SW // 2, SH - 100,
            arcade.color.GOLD, 36, bold=True,
            anchor_x="center"
        )
        self.back_text = Text(
            "Нажмите ESC для возврата в меню",
            SW // 2, 50,
            CLUI, 16,
            anchor_x="center"
        )
        self.empty_text = Text(
            "Рекордов пока нет!",
            SW // 2, SH // 2,
            CLUI, 24,
            anchor_x="center"
        )
        self.score_texts = []
        self.create_score_texts()

    def create_score_texts(self):
        self.score_texts = []
        if self.scores:
            y_position = SH - 180
            for i, (date, score, level) in enumerate(self.scores[:10], 1):
                color = arcade.color.GOLD if i == 1 else CLUI
                text_obj = Text(
                    f"{i}. {score} очков (Уровень {level}) - {date}",
                    SW // 2, y_position,
                    color, 18,
                    anchor_x="center"
                )
                self.score_texts.append(text_obj)
                y_position -= 40

    def load_scores(self):
        data_dir = Path(__file__).parent / "data"
        scores_file = data_dir / "scores.csv"
        if scores_file.exists():
            with open(scores_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)
                self.scores = list(reader)

    def on_show_view(self):
        arcade.set_background_color(CLB)

    def on_update(self, delta_time):
        self.star_field.update()

    def on_draw(self):
        self.clear()
        self.star_field.draw()
        self.title_text.draw()
        if self.scores:
            for text_obj in self.score_texts:
                text_obj.draw()
        else:
            self.empty_text.draw()
        self.back_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            menu_view = MenuView()
            self.window.show_view(menu_view)


def main():
    window = arcade.Window(SW, SH, SCT)
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
