import arcade
import random
import math
import csv
from pathlib import Path
from arcade import Text
import time

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Космический Шутер"
PLAYER_SPEED = 2
PLAYER_HEALTH = 100
PLAYER_FIRE_RATE = 0.15
ENEMY_SPEED = 2
ENEMY_SPAWN_INTERVAL = 2.0
BULLET_SPEED = 10
ENEMY_BULLET_SPEED = 5
LEVEL_1_SCORE = 500
LEVEL_2_SCORE = 1500
LEVEL_3_SCORE = 3000
LEVEL_4_SCORE = 5000
COLOR_BACKGROUND = arcade.color.BLACK
COLOR_UI = arcade.color.WHITE
COLOR_HEALTH_FULL = arcade.color.GREEN
COLOR_HEALTH_LOW = arcade.color.RED


class Particle:
    def __init__(self, x, y, col):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.col = col
        self.a = 255
        self.sz = random.randint(2, 5)
        self.lt = random.uniform(0.5, 1.5)
        self.age = 0

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.age += dt
        self.a = int(255 * (1 - self.age / self.lt))
        return self.age < self.lt

    def draw(self):
        if self.a > 0:
            arcade.draw_circle_filled(
                self.x, self.y, self.sz,
                self.col if isinstance(self.col, tuple) else arcade.color.WHITE
            )


class ParticleSystem:
    def __init__(self):
        self.parts = []

    def make_exp(self, x, y, col, cnt=20):
        for _ in range(cnt):
            self.parts.append(Particle(x, y, col))

    def update(self, dt):
        self.parts = [p for p in self.parts if p.update(dt)]

    def draw(self):
        for p in self.parts:
            p.draw()


class Player(arcade.Sprite):
    def __init__(self, tex=None):
        super().__init__()
        self.width = 40
        self.height = 50
        self.hp = PLAYER_HEALTH
        self.sc = 0
        self.ft = 0
        self.lvl = 1
        self.can_sh = True
        self.tx = tex or []
        self.si = 0
        if self.tx:
            self.texture = self.tx[self.si]
        else:
            self.texture = arcade.make_soft_square_texture(
                self.width, arcade.color.CYAN, outer_alpha=255
            )

    def set_skin(self, idx):
        if self.tx:
            self.si = idx % len(self.tx)
            self.texture = self.tx[self.si]

    def next_skin(self):
        if self.tx:
            self.si = (self.si + 1) % len(self.tx)
            self.texture = self.tx[self.si]

    def update(self, dt=1/60):
        super().update()
        self.center_x += self.change_x
        self.center_y += self.change_y
        if self.left < 0:
            self.left = 0
        elif self.right > SCREEN_WIDTH:
            self.right = SCREEN_WIDTH
        if self.bottom < 0:
            self.bottom = 0
        elif self.top > SCREEN_HEIGHT:
            self.top = SCREEN_HEIGHT

    def upd_fire(self, dt):
        if not self.can_sh:
            self.ft += dt
            if self.ft >= PLAYER_FIRE_RATE:
                self.can_sh = True
                self.ft = 0

    def hit(self, dmg):
        self.hp = max(0, self.hp - dmg)
        return self.hp <= 0


class Enemy(arcade.Sprite):
    def __init__(self, typ, lvl, tex=None):
        super().__init__()
        self.typ = typ
        self.width = 45
        self.height = 45
        bh = 20 + (lvl * 10)
        if typ == 'fast':
            self.mhp = int(bh * 0.7)
            self.spd = 1.5
            self.dmg = 10
            col = arcade.color.ORANGE
        elif typ == 'tank':
            self.mhp = int(bh * 1.8)
            self.spd = 0.7
            self.dmg = 25
            col = arcade.color.PURPLE
        else:
            self.mhp = bh
            self.spd = 1.0
            self.dmg = 15
            col = arcade.color.RED
        self.hp = self.mhp
        self.st = 0
        self.si = random.uniform(1.5, 3.0)
        if tex is not None:
            self.texture = tex
        else:
            self.texture = arcade.make_soft_circle_texture(
                self.width, col, outer_alpha=255
            )

    def update(self, dt=1/60):
        super().update()
        self.center_y -= ENEMY_SPEED * self.spd
        self.center_x += math.sin(self.center_y / 50) * 2

    def upd_shoot(self, dt):
        self.st += dt
        if self.st >= self.si:
            self.st = 0
            return True
        return False

    def hit(self, dmg):
        self.hp -= dmg
        return self.hp <= 0

    def draw_hp(self):
        if self.hp <= 0:
            return
        w = 40
        h = 5
        r = self.hp / self.mhp
        if r > 0.5:
            col = arcade.color.GREEN
        elif r > 0.25:
            col = arcade.color.YELLOW
        else:
            col = arcade.color.RED
        arcade.draw_lrbt_rectangle_filled(
            self.center_x - w / 2,
            self.center_x + w / 2,
            self.top + 8,
            self.top + 8 + h,
            arcade.color.DARK_RED
        )
        arcade.draw_lrbt_rectangle_filled(
            self.center_x - w / 2,
            self.center_x - w / 2 + w * r,
            self.top + 8,
            self.top + 8 + h,
            col
        )


class Boss(arcade.Sprite):
    def __init__(self, tex=None):
        super().__init__()
        self.width = 160
        self.height = 120
        self.mhp = 1500
        self.hp = self.mhp
        self.ph = 1
        self.dmg = 30
        self.st = 0
        self.tx = tex or []
        if self.tx:
            self.texture = self.tx[0]
        else:
            self.texture = arcade.make_soft_square_texture(
                max(self.width, self.height), arcade.color.DARK_RED, outer_alpha=255
            )

    def update(self):
        self.center_x += math.sin(time.time() * 1.5) * 2
        r = self.hp / self.mhp
        old = self.ph
        if r <= 0.33:
            self.ph = 3
        elif r <= 0.66:
            self.ph = 2
        else:
            self.ph = 1
        if self.tx and old != self.ph:
            idx = max(0, min(2, self.ph - 1))
            self.texture = self.tx[idx]

    def hit(self, dmg):
        self.hp -= dmg
        return self.hp <= 0


class Bullet(arcade.Sprite):
    def __init__(self, x, y, dmg, is_pl=True):
        super().__init__()
        self.width = 12
        self.height = 30
        self.is_pl = is_pl
        self.dmg = dmg
        col = arcade.color.YELLOW if is_pl else arcade.color.RED_ORANGE
        self.texture = arcade.make_soft_square_texture(
            max(self.width, self.height), col, outer_alpha=255
        )
        self.center_x = x
        self.center_y = y
        self.change_y = BULLET_SPEED if is_pl else -ENEMY_BULLET_SPEED


class PowerUp(arcade.Sprite):
    def __init__(self, x, y, typ, tex=None):
        super().__init__()
        self.typ = typ
        self.width = 30
        self.height = 30
        if tex is not None:
            self.texture = tex
        else:
            clr = {
                'health': arcade.color.GREEN,
                'speed': arcade.color.BLUE,
                'damage': arcade.color.ORANGE
            }
            col = clr.get(typ, arcade.color.WHITE)
            self.texture = arcade.make_soft_circle_texture(
                self.width, col, outer_alpha=200
            )
        self.center_x = x
        self.center_y = y
        self.change_y = -2


class StarField:
    def __init__(self, cnt=100):
        self.stars = []
        for _ in range(cnt):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            sp = random.uniform(0.5, 2)
            sz = random.randint(1, 3)
            self.stars.append({'x': x, 'y': y, 'sp': sp, 'sz': sz})

    def update(self):
        for s in self.stars:
            s['y'] -= s['sp']
            if s['y'] < 0:
                s['y'] = SCREEN_HEIGHT
                s['x'] = random.randint(0, SCREEN_WIDTH)

    def draw(self):
        for s in self.stars:
            arcade.draw_circle_filled(
                s['x'], s['y'], s['sz'],
                arcade.color.WHITE
            )


class Camera:
    def __init__(self):
        self.ox = 0
        self.oy = 0
        self.inv = 0
        self.dur = 0

    def shake(self, inv=10, dur=0.3):
        self.inv = inv
        self.dur = dur

    def update(self, dt):
        if self.dur > 0:
            self.dur -= dt
            self.ox = random.uniform(-self.inv, self.inv)
            self.oy = random.uniform(-self.inv, self.inv)
        else:
            self.ox = 0
            self.oy = 0


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.pl = None
        self.en_list = None
        self.bul_list = None
        self.pup_list = None
        self.ps = None
        self.stars = None
        self.cam = None
        self.est = 0
        self.pust = 0
        self.game_over = False
        self.paused = False
        self.cur_lvl = 1
        self.boss = None
        self.boss_fight = False
        self.boss_list = arcade.SpriteList()
        self.win = False
        self.setup_sounds()
        arcade.set_background_color(COLOR_BACKGROUND)
        self.pl_tx = []
        self.en_tx = []
        self.boss_tx = []
        self.pup_tx = {}

    def setup_sounds(self):
        pass

    def load_tex(self, pth, fb):
        try:
            if pth.exists():
                return arcade.load_texture(str(pth))
        except Exception:
            pass
        return fb()

    def setup(self):
        assets = Path(__file__).parent / "assets"
        pf = [assets / f"player_skin{i}.png" for i in (1, 2, 3)]
        def pfb():
            return arcade.make_soft_square_texture(40, arcade.color.CYAN, outer_alpha=255)
        self.pl_tx = [self.load_tex(p, pfb) for p in pf]
        ef = [assets / f"enemy_skin{i}.png" for i in (1, 2, 3)]
        def efb():
            return arcade.make_soft_circle_texture(45, arcade.color.RED, outer_alpha=255)
        self.en_tx = [self.load_tex(p, efb) for p in ef]
        bf = [assets / f"boss_phase{i}.png" for i in (1, 2, 3)]
        def bfb():
            return arcade.make_soft_square_texture(160, arcade.color.DARK_RED, outer_alpha=255)
        self.boss_tx = [self.load_tex(p, bfb) for p in bf]
        pm = {
            'health': assets / 'powerup_health.png',
            'speed': assets / 'powerup_speed.png',
            'damage': assets / 'powerup_damage.png'
        }
        def hfb():
            return arcade.make_soft_circle_texture(30, arcade.color.GREEN, outer_alpha=200)
        def sfb():
            return arcade.make_soft_circle_texture(30, arcade.color.BLUE, outer_alpha=200)
        def dfb():
            return arcade.make_soft_circle_texture(30, arcade.color.ORANGE, outer_alpha=200)
        self.pup_tx = {
            'health': self.load_tex(pm['health'], hfb),
            'speed': self.load_tex(pm['speed'], sfb),
            'damage': self.load_tex(pm['damage'], dfb),
        }
        self.pl = Player(tex=self.pl_tx)
        self.pl.center_x = SCREEN_WIDTH // 2
        self.pl.center_y = 100
        self.pl_list = arcade.SpriteList()
        self.pl_list.append(self.pl)
        self.en_list = arcade.SpriteList()
        self.bul_list = arcade.SpriteList()
        self.pup_list = arcade.SpriteList()
        self.ps = ParticleSystem()
        self.stars = StarField(150)
        self.cam_sprites = arcade.camera.Camera2D()
        self.shake = Camera()
        self.est = 0
        self.pust = 0
        self.game_over = False
        self.paused = False
        self.cur_lvl = 1
        self.hp_txt = Text(
            f"HP: {self.pl.hp}",
            10, SCREEN_HEIGHT - 20,
            arcade.color.GREEN, 18, bold=True
        )
        self.sc_txt = Text(
            f"Счёт: {self.pl.sc}",
            10, SCREEN_HEIGHT - 60,
            COLOR_UI, 18, bold=True
        )
        self.lvl_txt = Text(
            f"Уровень: {self.cur_lvl}",
            10, SCREEN_HEIGHT - 90,
            COLOR_UI, 18, bold=True
        )
        self.ctrl_txt = Text(
            "WASD - движение | SPACE - стрельба | P - пауза | C - смена скина игрока",
            SCREEN_WIDTH // 2, 20,
            COLOR_UI, 12,
            anchor_x="center"
        )
        self.go_title = Text(
            "ИГРА ОКОНЧЕНА",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80,
            arcade.color.RED, 36, bold=True,
            anchor_x="center"
        )
        self.go_sc = Text(
            "",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20,
            COLOR_UI, 24,
            anchor_x="center"
        )
        self.go_lvl = Text(
            "",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20,
            COLOR_UI, 20,
            anchor_x="center"
        )
        self.go_hint = Text(
            "Нажмите ENTER для возврата в меню",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80,
            COLOR_UI, 16,
            anchor_x="center"
        )
        self.pause_title = Text(
            "ПАУЗА",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20,
            COLOR_UI, 32, bold=True,
            anchor_x="center"
        )
        self.pause_hint = Text(
            "Нажмите P для продолжения",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30,
            COLOR_UI, 16,
            anchor_x="center"
        )

    def spawn_en(self):
        typs = ['basic', 'fast', 'tank']
        wts = [0.6, 0.25, 0.15]
        t = random.choices(typs, weights=wts)[0]
        tx = None
        if self.en_tx:
            tx = random.choice(self.en_tx)
        e = Enemy(t, self.cur_lvl, tex=tx)
        e.center_x = random.randint(50, SCREEN_WIDTH - 50)
        e.center_y = SCREEN_HEIGHT + 30
        self.en_list.append(e)

    def start_boss(self):
        self.en_list.clear()
        self.bul_list.clear()
        self.pup_list.clear()
        self.est = 0
        self.pust = 0
        self.boss = Boss(tex=self.boss_tx)
        self.boss.center_x = SCREEN_WIDTH // 2
        self.boss.center_y = SCREEN_HEIGHT - 120
        self.boss_list.clear()
        self.boss_list.append(self.boss)
        self.boss_fight = True
        self.win = False

    def spawn_pup(self):
        typs = ['health', 'speed', 'damage']
        t = random.choice(typs)
        tx = self.pup_tx.get(t)
        p = PowerUp(
            random.randint(50, SCREEN_WIDTH - 50),
            SCREEN_HEIGHT + 30,
            t,
            tex=tx
        )
        self.pup_list.append(p)

    def upd_lvl(self):
        old = self.cur_lvl
        if self.pl.sc >= LEVEL_4_SCORE:
            self.cur_lvl = 4
        elif self.pl.sc >= LEVEL_3_SCORE:
            self.cur_lvl = 3
        elif self.pl.sc >= LEVEL_2_SCORE:
            self.cur_lvl = 2
        elif self.pl.sc >= LEVEL_1_SCORE:
            self.cur_lvl = 1
        if old != self.cur_lvl:
            self.ps.make_exp(
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                arcade.color.GOLD,
                80
            )
            if self.cur_lvl == 4:
                self.start_boss()

    def on_update(self, dt):
        if self.game_over or self.paused:
            return
        self.stars.update()
        self.shake.update(dt)
        self.pl.update()
        self.pl.upd_fire(dt)
        self.upd_lvl()
        if self.boss_fight and self.boss:
            self.boss.update()
            self.boss.st += dt
            if self.boss.ph == 1 and self.boss.st > 1.0:
                for ang in [-45, -30, -15, 0, 15, 30, 45]:
                    b = Bullet(
                        self.boss.center_x,
                        self.boss.bottom,
                        dmg=35,
                        is_pl=False
                    )
                    b.change_x = math.sin(math.radians(ang)) * 6
                    b.change_y = -BULLET_SPEED
                    self.bul_list.append(b)
                self.boss.st = 0
            elif self.boss.ph == 2 and self.boss.st > 0.8:
                for ang in range(0, 360, 20):
                    b = Bullet(
                        self.boss.center_x,
                        self.boss.center_y,
                        dmg=40,
                        is_pl=False
                    )
                    b.change_x = math.cos(math.radians(ang)) * 6
                    b.change_y = math.sin(math.radians(ang)) * 6
                    self.bul_list.append(b)
                self.boss.st = 0
            elif self.boss.ph == 3 and self.boss.st > 0.5:
                for _ in range(12):
                    b = Bullet(
                        random.randint(100, SCREEN_WIDTH - 100),
                        self.boss.bottom,
                        dmg=50,
                        is_pl=False
                    )
                    b.change_y = -10
                    b.change_x = random.uniform(-3, 3)
                    self.bul_list.append(b)
                self.boss.st = 0
        self.en_list.update()
        for e in self.en_list:
            if e.upd_shoot(dt):
                b = Bullet(
                    e.center_x,
                    e.center_y,
                    dmg=e.dmg,
                    is_pl=False
                )
                self.bul_list.append(b)
        self.bul_list.update()
        self.pup_list.update()
        self.ps.update(dt)
        if not self.boss_fight:
            self.est += dt
            si = max(0.8, ENEMY_SPAWN_INTERVAL - self.cur_lvl * 0.2)
            if self.est >= si:
                self.spawn_en()
                self.est = 0
        self.pust += dt
        if self.pust >= 10:
            self.spawn_pup()
            self.pust = 0
        for b in list(self.bul_list):
            if b.is_pl:
                hits = arcade.check_for_collision_with_list(b, self.en_list)
                if self.boss_fight and self.boss:
                    if arcade.check_for_collision(b, self.boss):
                        if self.boss.hit(b.dmg):
                            self.ps.make_exp(
                                self.boss.center_x,
                                self.boss.center_y,
                                arcade.color.GOLD,
                                200
                            )
                            self.pl.sc += 5000
                            self.boss_list.clear()
                            self.boss = None
                            self.boss_fight = False
                            self.win = True
                            self.game_over = True
                            self.save_sc()
                        b.remove_from_sprite_lists()
                        break
                if hits:
                    for e in hits:
                        if e.hit(b.dmg):
                            self.ps.make_exp(e.center_x, e.center_y, arcade.color.ORANGE)
                            e.remove_from_sprite_lists()
                            self.pl.sc += 50
                    b.remove_from_sprite_lists()
                    break
        for b in list(self.bul_list):
            if not b.is_pl:
                if arcade.check_for_collision(b, self.pl):
                    if self.pl.hit(b.dmg):
                        self.game_over = True
                        self.save_sc()
                    b.remove_from_sprite_lists()
                    self.shake.shake(8, 0.3)
        hits = arcade.check_for_collision_with_list(self.pl, self.en_list)
        for e in hits:
            if self.pl.hit(e.dmg):
                self.game_over = True
                self.save_sc()
            e.remove_from_sprite_lists()
            self.ps.make_exp(
                e.center_x, e.center_y,
                arcade.color.RED, 20
            )
            self.shake.shake(10, 0.4)
        pups = arcade.check_for_collision_with_list(self.pl, self.pup_list)
        for p in pups:
            if p.typ == 'health':
                self.pl.hp = min(PLAYER_HEALTH, self.pl.hp + 30)
            p.remove_from_sprite_lists()
        for e in list(self.en_list):
            if e.top < 0:
                e.remove_from_sprite_lists()
        for b in list(self.bul_list):
            if b.bottom > SCREEN_HEIGHT or b.top < 0:
                b.remove_from_sprite_lists()
        for p in list(self.pup_list):
            if p.top < 0:
                p.remove_from_sprite_lists()
        self.upd_lvl()

    def on_draw(self):
        self.clear()
        cx = SCREEN_WIDTH // 2 + self.shake.ox
        cy = SCREEN_HEIGHT // 2 + self.shake.oy
        self.cam_sprites.position = (cx, cy)
        with self.cam_sprites.activate():
            self.stars.draw()
            self.bul_list.draw()
            self.en_list.draw()
            if self.boss_fight:
                self.boss_list.draw()
            for e in self.en_list:
                e.draw_hp()
            self.pup_list.draw()
            self.pl_list.draw()
            self.ps.draw()
        self.draw_ui()
        if self.game_over:
            self.draw_go()
        if self.paused:
            self.draw_pause()

    def draw_ui(self):
        r = self.pl.hp / PLAYER_HEALTH
        col = COLOR_HEALTH_FULL if r > 0.3 else COLOR_HEALTH_LOW
        self.hp_txt.text = f"HP: {self.pl.hp}"
        self.hp_txt.color = col
        self.hp_txt.draw()
        w = max(0, 200 * r)
        arcade.draw_lrbt_rectangle_filled(
            0, w, SCREEN_HEIGHT - 39, SCREEN_HEIGHT - 24,
            col
        )
        arcade.draw_lrbt_rectangle_outline(
            0, 200, SCREEN_HEIGHT - 39, SCREEN_HEIGHT - 24,
            COLOR_UI, 2
        )
        self.sc_txt.text = f"Счёт: {self.pl.sc}"
        self.sc_txt.draw()
        self.lvl_txt.text = f"Уровень: {self.cur_lvl}"
        self.lvl_txt.draw()
        self.ctrl_txt.draw()
        if self.boss_fight and self.boss is not None:
            w = 600
            h = 20
            cx = SCREEN_WIDTH // 2
            cy = SCREEN_HEIGHT - 50
            arcade.draw_lrbt_rectangle_filled(
                left=cx - w / 2,
                right=cx + w / 2,
                bottom=cy - h / 2,
                top=cy + h / 2,
                color=arcade.color.BLACK
            )
            r = max(0, self.boss.hp / self.boss.mhp)
            cw = w * r
            if cw > 0:
                arcade.draw_lrbt_rectangle_filled(
                    left=cx - w / 2,
                    right=cx - w / 2 + cw,
                    bottom=cy - h / 2,
                    top=cy + h / 2,
                    color=arcade.color.RED
                )
            arcade.draw_lrbt_rectangle_outline(
                left=cx - w / 2,
                right=cx + w / 2,
                bottom=cy - h / 2,
                top=cy + h / 2,
                color=arcade.color.WHITE,
                border_width=2
            )
            arcade.draw_text("ФИНАЛЬНЫЙ БОСС", cx, cy + 20, arcade.color.WHITE, 12, anchor_x="center")

    def draw_go(self):
        arcade.draw_lrbt_rectangle_filled(
            SCREEN_WIDTH // 2 - 200, SCREEN_WIDTH // 2 + 200,
            SCREEN_HEIGHT // 2 - 150, SCREEN_HEIGHT // 2 + 150,
            COLOR_BACKGROUND.replace(a=230)
        )
        if getattr(self, "win", False):
            t = "ПОБЕДА!"
            col = arcade.color.GOLD
        else:
            t = "ИГРА ОКОНЧЕНА"
            col = arcade.color.RED
        arcade.draw_text(t,
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80,
                         col, 36, bold=True, anchor_x="center")
        self.go_sc.text = f"Ваш счёт: {self.pl.sc}"
        self.go_lvl.text = f"Достигнутый уровень: {self.cur_lvl}"
        self.go_sc.draw()
        self.go_lvl.draw()
        self.go_hint.draw()

    def draw_pause(self):
        arcade.draw_lrbt_rectangle_filled(
            SCREEN_WIDTH // 2 - 150, SCREEN_WIDTH // 2 + 150,
            SCREEN_HEIGHT // 2 - 75, SCREEN_HEIGHT // 2 + 75,
            COLOR_BACKGROUND.replace(a=200)
        )
        self.pause_title.draw()
        self.pause_hint.draw()

    def on_key_press(self, key, mod):
        if self.game_over:
            if key == arcade.key.ENTER:
                v = MenuView()
                self.window.show_view(v)
            return
        if key == arcade.key.P:
            self.paused = not self.paused
            return
        if self.paused:
            return
        if key == arcade.key.W:
            self.pl.change_y = PLAYER_SPEED
        elif key == arcade.key.S:
            self.pl.change_y = -PLAYER_SPEED
        elif key == arcade.key.A:
            self.pl.change_x = -PLAYER_SPEED
        elif key == arcade.key.D:
            self.pl.change_x = PLAYER_SPEED
        elif key == arcade.key.SPACE:
            if self.pl.can_sh:
                b = Bullet(
                    self.pl.center_x,
                    self.pl.top,
                    dmg=20,
                    is_pl=True
                )
                self.bul_list.append(b)
                self.pl.can_sh = False
        elif key == arcade.key.C:
            self.pl.next_skin()

    def on_key_release(self, key, mod):
        if key in (arcade.key.W, arcade.key.S):
            self.pl.change_y = 0
        elif key in (arcade.key.A, arcade.key.D):
            self.pl.change_x = 0

    def save_sc(self):
        d = Path(__file__).parent / "data"
        d.mkdir(exist_ok=True)
        f = d / "scores.csv"
        sc = []
        if f.exists():
            with open(f, 'r', encoding='utf-8') as fl:
                r = csv.reader(fl)
                next(r, None)
                sc = list(r)
        import datetime
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sc.append([ts, str(self.pl.sc), str(self.cur_lvl)])
        sc.sort(key=lambda x: int(x[1]), reverse=True)
        with open(f, 'w', encoding='utf-8', newline='') as fl:
            w = csv.writer(fl)
            w.writerow(['Дата', 'Счёт', 'Уровень'])
            w.writerows(sc[:10])


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.stars = StarField(100)
        self.title = Text(
            "КОСМИЧЕСКИЙ ШУТЕР",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150,
            arcade.color.CYAN, 48, bold=True,
            anchor_x="center"
        )
        self.start = Text(
            "Нажмите ENTER для начала игры",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            COLOR_UI, 24,
            anchor_x="center"
        )
        self.hs = Text(
            "Нажмите H для просмотра рекордов",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50,
            COLOR_UI, 20,
            anchor_x="center"
        )
        self.ctrl = Text(
            "Управление: WASD - движение, SPACE - стрельба",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120,
            arcade.color.LIGHT_GRAY, 16,
            anchor_x="center"
        )
        self.goal = Text(
            "Цель: уничтожайте врагов и набирайте очки!",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 160,
            arcade.color.LIGHT_GRAY, 16,
            anchor_x="center"
        )

    def on_show_view(self):
        arcade.set_background_color(COLOR_BACKGROUND)

    def on_update(self, dt):
        self.stars.update()

    def on_draw(self):
        self.clear()
        self.stars.draw()
        self.title.draw()
        self.start.draw()
        self.hs.draw()
        self.ctrl.draw()
        self.goal.draw()

    def on_key_press(self, key, mod):
        if key == arcade.key.ENTER:
            g = GameView()
            g.setup()
            self.window.show_view(g)
        elif key == arcade.key.H:
            h = HighScoreView()
            self.window.show_view(h)


class HighScoreView(arcade.View):
    def __init__(self):
        super().__init__()
        self.stars = StarField(100)
        self.sc = []
        self.load()
        self.title = Text(
            "ТАБЛИЦА РЕКОРДОВ",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
            arcade.color.GOLD, 36, bold=True,
            anchor_x="center"
        )
        self.back = Text(
            "Нажмите ESC для возврата в меню",
            SCREEN_WIDTH // 2, 50,
            COLOR_UI, 16,
            anchor_x="center"
        )
        self.empty = Text(
            "Рекордов пока нет!",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            COLOR_UI, 24,
            anchor_x="center"
        )
        self.txs = []
        self.make_txs()

    def make_txs(self):
        self.txs = []
        if self.sc:
            y = SCREEN_HEIGHT - 180
            for i, (d, s, l) in enumerate(self.sc[:10], 1):
                col = arcade.color.GOLD if i == 1 else COLOR_UI
                t = Text(
                    f"{i}. {s} очков (Уровень {l}) - {d}",
                    SCREEN_WIDTH // 2, y,
                    col, 18,
                    anchor_x="center"
                )
                self.txs.append(t)
                y -= 40

    def load(self):
        d = Path(__file__).parent / "data"
        f = d / "scores.csv"
        if f.exists():
            with open(f, 'r', encoding='utf-8') as fl:
                r = csv.reader(fl)
                next(r, None)
                self.sc = list(r)

    def on_show_view(self):
        arcade.set_background_color(COLOR_BACKGROUND)

    def on_update(self, dt):
        self.stars.update()

    def on_draw(self):
        self.clear()
        self.stars.draw()
        self.title.draw()
        if self.sc:
            for t in self.txs:
                t.draw()
        else:
            self.empty.draw()
        self.back.draw()

    def on_key_press(self, key, mod):
        if key == arcade.key.ESCAPE:
            v = MenuView()
            self.window.show_view(v)


def main():
    w = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    v = MenuView()
    w.show_view(v)
    arcade.run()


if __name__ == "__main__":
    main()
