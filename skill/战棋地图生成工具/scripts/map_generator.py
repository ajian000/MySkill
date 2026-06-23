"""
战棋地图生成工具 - 核心脚本
用于生成类火焰纹章风格的正方形网格战棋地图。
支持随机生成、手动编辑、JSON/ASCII/PNG 输出。

用法:
  python map_generator.py --rows 20 --cols 25 --water 0.1 --forest 0.15
  python map_generator.py --edit 地图.json --terrain 3,5=forest
  python map_generator.py --rows 15 --cols 20 --random --seed 42
"""

import json
import os
import random
import sys
import argparse
from collections import deque

# ============================================================
# 地形定义
# ============================================================
TERRAINS = {
    "plain":    {"name": "平原", "move_cost": 1, "avoid": 0,  "defense": 0, "color": (144, 238, 144), "passable": True,  "symbol": "·"},
    "forest":   {"name": "森林", "move_cost": 2, "avoid": 20, "defense": 1, "color": (34, 139, 34),   "passable": True,  "symbol": "木"},
    "mountain": {"name": "山地", "move_cost": 3, "avoid": 10, "defense": 2, "color": (139, 69, 19),   "passable": True,  "symbol": "山"},
    "river":    {"name": "河流", "move_cost": 0, "avoid": 0,  "defense": 0, "color": (65, 105, 225),  "passable": False, "symbol": "～"},
    "bridge":   {"name": "桥梁", "move_cost": 1, "avoid": 0,  "defense": 0, "color": (222, 184, 135), "passable": True,  "symbol": "桥"},
    "road":     {"name": "道路", "move_cost": 1, "avoid": 0,  "defense": 0, "color": (210, 180, 140), "passable": True,  "symbol": "路"},
    "wall":     {"name": "城墙", "move_cost": 0, "avoid": 0,  "defense": 0, "color": (128, 128, 128), "passable": False, "symbol": "墙"},
    "castle":   {"name": "城堡", "move_cost": 1, "avoid": 30, "defense": 3, "color": (255, 215, 0),   "passable": True,  "symbol": "城"},
    "village":  {"name": "村庄", "move_cost": 1, "avoid": 10, "defense": 1, "color": (255, 99, 71),   "passable": True,  "symbol": "村"},
    "fort":     {"name": "要塞", "move_cost": 1, "avoid": 20, "defense": 2, "color": (220, 20, 60),   "passable": True,  "symbol": "堡"},
    "ruins":    {"name": "废墟", "move_cost": 1, "avoid": 5,  "defense": 0, "color": (160, 82, 45),   "passable": True,  "symbol": "墟"},
    "desert":   {"name": "沙漠", "move_cost": 2, "avoid": 0,  "defense": 0, "color": (244, 164, 96),  "passable": True,  "symbol": "沙"},
    "snow":     {"name": "雪地", "move_cost": 2, "avoid": 0,  "defense": 0, "color": (240, 248, 255), "passable": True,  "symbol": "雪"},
    "abyss":    {"name": "深渊", "move_cost": 0, "avoid": 0,  "defense": 0, "color": (47, 47, 47),    "passable": False, "symbol": "渊"},
    "sea":      {"name": "海洋", "move_cost": 0, "avoid": 0,  "defense": 0, "color": (30, 144, 255),  "passable": False, "symbol": "海"},
}

# 基础地形权重（用于随机生成时的地形分布）
TERRAIN_WEIGHTS = {
    "plain":    35,
    "forest":   15,
    "mountain": 10,
    "river":    8,
    "road":     5,
    "desert":   5,
    "snow":     5,
    "abyss":    2,
}


class TacticalMap:
    """战棋地图类"""

    def __init__(self, rows=15, cols=20, name="未命名地图"):
        self.rows = rows
        self.cols = cols
        self.name = name
        self.grid = [["plain" for _ in range(cols)] for _ in range(rows)]
        self.player_start_zone = []
        self.enemy_zone = []
        self.npc_positions = []
        self.player_units = []
        self.enemy_units = []
        self.victory_condition = {
            "type": "seize",
            "target": None,
            "extra_conditions": []
        }
        self.turn_limit = 20
        self.difficulty = "中等"

    def set_terrain(self, row, col, terrain_id):
        """设置指定格子的地形"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            if terrain_id in TERRAINS:
                self.grid[row][col] = terrain_id
                return True
        return False

    def get_terrain(self, row, col):
        """获取指定格子的地形"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        return None

    def is_passable(self, row, col):
        """判断格子是否可通行"""
        terrain = self.get_terrain(row, col)
        if terrain:
            return TERRAINS[terrain]["passable"]
        return False

    def add_player_start_zone(self, cells):
        """添加我方起始区域"""
        self.player_start_zone.append(cells)

    def add_enemy_zone(self, cells):
        """添加敌方布防区域"""
        self.enemy_zone.append(cells)

    def add_npc_position(self, row, col):
        """添加 NPC 位置"""
        self.npc_positions.append([row, col])

    def add_player_unit(self, row, col, unit_class="领主", level=1):
        """添加我方单位参考位置"""
        self.player_units.append({
            "位置": [row, col],
            "推荐职业": unit_class,
            "等级": level
        })

    def add_enemy_unit(self, row, col, unit_class="剑兵", level=1):
        """添加敌方单位参考位置"""
        self.enemy_units.append({
            "位置": [row, col],
            "推荐职业": unit_class,
            "等级": level
        })

    def to_dict(self):
        """导出为字典（可用于 JSON 序列化）"""
        grid_data = []
        for r in range(self.rows):
            for c in range(self.cols):
                grid_data.append({
                    "行": r, "列": c,
                    "地形": self.grid[r][c],
                    "高度": 0
                })

        return {
            "地图名称": self.name,
            "地图尺寸": {"行": self.rows, "列": self.cols},
            "网格类型": "正方形",
            "胜利条件": self.victory_condition["type"],
            "地形数据": grid_data,
            "我方起始区域": self.player_start_zone,
            "敌方布防区域": self.enemy_zone,
            "NPC位置": self.npc_positions,
            "我方单位参考": self.player_units,
            "敌方单位参考": self.enemy_units,
            "胜利条件": self.victory_condition,
            "回合限制": self.turn_limit,
            "难度": self.difficulty
        }

    def save_json(self, filepath):
        """保存为 JSON 文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"[OK] JSON 地图已保存: {filepath}")

    def save_ascii(self, filepath):
        """保存为 ASCII 文本地图"""
        lines = []
        lines.append(f"地图: {self.name}")
        lines.append(f"尺寸: {self.rows}x{self.cols}")
        lines.append(f"网格: 正方形")
        lines.append("")

        # 列号标头
        header = "    " + "".join(chr(ord('A') + c) if c < 26 else chr(ord('a') + c - 26) for c in range(self.cols))
        lines.append(header)

        for r in range(self.rows):
            row_str = f"{r:3d} "
            for c in range(self.cols):
                terrain = self.grid[r][c]
                row_str += TERRAINS[terrain]["symbol"]
            lines.append(row_str)

        # 区域信息
        lines.append("")
        lines.append("--- 区域信息 ---")
        if self.player_start_zone:
            lines.append(f"我方起始区: {len(self.player_start_zone)} 格")
        if self.enemy_zone:
            lines.append(f"敌方布防区: {len(self.enemy_zone)} 格")
        if self.npc_positions:
            lines.append(f"NPC 位置: {len(self.npc_positions)} 处")

        # 图例
        lines.append("")
        lines.append("--- 图例 ---")
        for tid, tdata in TERRAINS.items():
            lines.append(f"  {tdata['symbol']} = {tdata['name']}")

        result = "\n".join(lines)
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"[OK] ASCII 地图已保存: {filepath}")
        return result

    def save_png(self, filepath):
        """保存为 PNG 可视化图片（需要 Pillow）"""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            print("[!] 请先安装 Pillow: pip install Pillow")
            return

        cell_size = 32
        margin = 40
        width = self.cols * cell_size + margin * 2
        height = self.rows * cell_size + margin * 2

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # 尝试加载字体
        font = None
        try:
            font = ImageFont.truetype("simhei.ttf", 14)
        except Exception:
            try:
                font = ImageFont.truetype("msyh.ttc", 14)
            except Exception:
                font = ImageFont.load_default()

        # 绘制标题
        draw.text((margin, 5), f"{self.name}  ({self.rows}×{self.cols})", fill=(0, 0, 0), font=font)

        # 绘制网格
        for r in range(self.rows):
            for c in range(self.cols):
                x1 = margin + c * cell_size
                y1 = margin + r * cell_size + 20
                x2 = x1 + cell_size
                y2 = y1 + cell_size

                terrain = self.grid[r][c]
                color = TERRAINS[terrain]["color"]
                draw.rectangle([x1, y1, x2, y2], fill=color, outline=(0, 0, 0))

                # 在特殊地形上标记符号
                symbol = TERRAINS[terrain]["symbol"]
                if symbol and font:
                    draw.text((x1 + 8, y1 + 8), symbol, fill=(0, 0, 0), font=font)

        # 图例（仅地形）
        legend_x = width - 120
        legend_y = 5
        draw.text((legend_x, legend_y), "图例:", fill=(0, 0, 0), font=font)
        y_offset = legend_y + 18
        for tid, tdata in TERRAINS.items():
            draw.rectangle([legend_x, y_offset, legend_x + 12, y_offset + 12],
                          fill=tdata["color"], outline=(0, 0, 0))
            draw.text((legend_x + 16, y_offset), tdata["name"], fill=(0, 0, 0), font=font)
            y_offset += 15
            if y_offset > height - 10:
                break

        img.save(filepath)
        print(f"[OK] PNG 图片已保存: {filepath}")

    def save_route_map(self, filepath):
        """生成进攻路线参考图，标明玩家出生位置、敌方布防位置和推荐进攻路线（需要 Pillow）"""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            print("[!] 请先安装 Pillow: pip install Pillow")
            return

        cell_size = 32
        margin = 40
        width = self.cols * cell_size + margin * 2
        height = self.rows * cell_size + margin + 60

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        font = None
        try:
            font = ImageFont.truetype("simhei.ttf", 14)
        except Exception:
            try:
                font = ImageFont.truetype("msyh.ttc", 14)
            except Exception:
                font = ImageFont.load_default()

        # 标题
        draw.text((margin, 5), f"{self.name} - 进攻路线参考图", fill=(0, 0, 0), font=font)

        # 绘制地形网格（浅色/半透明风格）
        for r in range(self.rows):
            for c in range(self.cols):
                x1 = margin + c * cell_size
                y1 = margin + r * cell_size + 20
                x2 = x1 + cell_size
                y2 = y1 + cell_size

                terrain = self.grid[r][c]
                color = TERRAINS[terrain]["color"]
                # 浅色背景
                light_color = tuple(min(255, c + 60) for c in color)
                draw.rectangle([x1, y1, x2, y2], fill=light_color, outline=(200, 200, 200))

        # 绘制我方起始区域（绿色填充半透明）
        for cell in self.player_start_zone:
            if len(cell) == 2:
                r, c = cell
                x1 = margin + c * cell_size
                y1 = margin + r * cell_size + 20
                draw.rectangle([x1, y1, x1 + cell_size - 1, y1 + cell_size - 1],
                              fill=(144, 238, 144), outline=(0, 180, 0), width=2)

        # 绘制敌方区域（红色填充半透明）
        for cell in self.enemy_zone:
            if len(cell) == 2:
                r, c = cell
                x1 = margin + c * cell_size
                y1 = margin + r * cell_size + 20
                draw.rectangle([x1, y1, x1 + cell_size - 1, y1 + cell_size - 1],
                              fill=(255, 200, 200), outline=(220, 0, 0), width=2)

        # 标记玩家出生锚点（绿色五角星简化为大圆点 + 标签）
        if self.player_start_zone:
            # 取起始区域中心
            avg_r = int(sum(c[0] for c in self.player_start_zone) / len(self.player_start_zone))
            avg_c = int(sum(c[1] for c in self.player_start_zone) / len(self.player_start_zone))
            cx = margin + avg_c * cell_size + cell_size // 2
            cy = margin + avg_r * cell_size + 20 + cell_size // 2
            draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(0, 180, 0), outline=(0, 80, 0), width=2)
            draw.text((cx - 20, cy - 28), "玩家出生", fill=(0, 120, 0), font=font)

        # 标记敌方布防锚点（红色大圆点 + 标签）
        if self.enemy_zone:
            avg_r = int(sum(c[0] for c in self.enemy_zone) / len(self.enemy_zone))
            avg_c = int(sum(c[1] for c in self.enemy_zone) / len(self.enemy_zone))
            cx = margin + avg_c * cell_size + cell_size // 2
            cy = margin + avg_r * cell_size + 20 + cell_size // 2
            draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(220, 0, 0), outline=(120, 0, 0), width=2)
            draw.text((cx - 20, cy - 28), "敌方布防", fill=(180, 0, 0), font=font)

        # 绘制我方单位参考位置（红色边框 + 蓝色填充圆形）
        for unit in self.player_units:
            pos = unit.get("位置")
            if pos and len(pos) == 2:
                r, c = pos
                cx = margin + c * cell_size + cell_size // 2
                cy = margin + r * cell_size + 20 + cell_size // 2
                draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10],
                            outline=(220, 0, 0), width=2)
                draw.ellipse([cx - 7, cy - 7, cx + 7, cy + 7],
                            fill=(65, 105, 225), outline=(220, 0, 0), width=1)
                unit_class = unit.get("推荐职业", "")
                if unit_class and font:
                    draw.text((cx + 12, cy - 8), unit_class, fill=(0, 0, 0), font=font)

        # 绘制敌方单位参考位置（黑色边框 + 红色填充圆形，每个代表 3-5 单位集群）
        for unit in self.enemy_units:
            pos = unit.get("位置")
            if pos and len(pos) == 2:
                r, c = pos
                cx = margin + c * cell_size + cell_size // 2
                cy = margin + r * cell_size + 20 + cell_size // 2
                draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10],
                            outline=(0, 0, 0), width=2)
                draw.ellipse([cx - 7, cy - 7, cx + 7, cy + 7],
                            fill=(220, 20, 60), outline=(0, 0, 0), width=1)
                if font:
                    draw.text((cx + 12, cy - 8), "x3-5", fill=(180, 0, 0), font=font)

        # 使用 BFS 计算推荐进攻路线
        route_path = self._calc_attack_route()
        if route_path:
            # 绘制路径（箭头线）
            for i in range(1, len(route_path)):
                pr, pc = route_path[i - 1]
                nr, nc = route_path[i]
                x1 = margin + pc * cell_size + cell_size // 2
                y1 = margin + pr * cell_size + 20 + cell_size // 2
                x2 = margin + nc * cell_size + cell_size // 2
                y2 = margin + nr * cell_size + 20 + cell_size // 2
                draw.line([(x1, y1), (x2, y2)], fill=(255, 140, 0), width=4)

                # 在路径点上画小圆
                draw.ellipse([x1 - 3, y1 - 3, x1 + 3, y1 + 3], fill=(255, 140, 0))

            # 最后一个点
            if route_path:
                lr, lc = route_path[-1]
                lx = margin + lc * cell_size + cell_size // 2
                ly = margin + lr * cell_size + 20 + cell_size // 2
                draw.ellipse([lx - 3, ly - 3, lx + 3, ly + 3], fill=(255, 140, 0))

            # 添加路线的图例标注
            draw.text((margin, height - 40), "━━ 推荐进攻路线", fill=(255, 140, 0), font=font)
        else:
            draw.text((margin, height - 40), "未找到可行的进攻路线", fill=(180, 0, 0), font=font)

        # 图例
        draw.rectangle([width - 200, 5, width - 188, 17], fill=(144, 238, 144), outline=(0, 180, 0))
        draw.text((width - 184, 5), "玩家区域", fill=(0, 0, 0), font=font)
        draw.rectangle([width - 200, 23, width - 188, 35], fill=(255, 200, 200), outline=(220, 0, 0))
        draw.text((width - 184, 23), "敌方区域", fill=(0, 0, 0), font=font)
        draw.text((width - 200, 41), "●", fill=(255, 140, 0), font=font)
        draw.text((width - 184, 41), "进攻路线", fill=(0, 0, 0), font=font)
        # 单位图标图例
        draw.ellipse([width - 200, 59, width - 188, 71],
                    outline=(220, 0, 0), width=2)
        draw.ellipse([width - 199, 60, width - 189, 70],
                    fill=(65, 105, 225), outline=(220, 0, 0), width=1)
        draw.text((width - 184, 59), "我方单位", fill=(0, 0, 0), font=font)
        draw.ellipse([width - 200, 77, width - 188, 89],
                    outline=(0, 0, 0), width=2)
        draw.ellipse([width - 199, 78, width - 189, 88],
                    fill=(220, 20, 60), outline=(0, 0, 0), width=1)
        draw.text((width - 184, 77), "敌方集群(3-5)", fill=(0, 0, 0), font=font)

        img.save(filepath)
        print(f"[OK] 进攻路线参考图已保存: {filepath}")

    def _calc_attack_route(self):
        """使用 BFS 计算从玩家起始区到敌方布防区的推荐进攻路线"""
        if not self.player_start_zone or not self.enemy_zone:
            return []

        rows, cols = self.rows, self.cols

        # 起始 = 玩家区中心
        sr = int(sum(c[0] for c in self.player_start_zone) / len(self.player_start_zone))
        sc = int(sum(c[1] for c in self.player_start_zone) / len(self.player_start_zone))
        start = (sr, sc)

        # 目标 = 敌方区中心
        er = int(sum(c[0] for c in self.enemy_zone) / len(self.enemy_zone))
        ec = int(sum(c[1] for c in self.enemy_zone) / len(self.enemy_zone))
        end = (er, ec)

        if not self.is_passable(sr, sc) or not self.is_passable(er, ec):
            return []

        # BFS 寻路
        parent = {start: None}
        queue = deque([start])

        while queue:
            r, c = queue.popleft()
            if (r, c) == end:
                break
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < rows and 0 <= nc < cols and
                        (nr, nc) not in parent and
                        self.is_passable(nr, nc)):
                    parent[(nr, nc)] = (r, c)
                    queue.append((nr, nc))

        if end not in parent:
            return []

        # 回溯路径
        path = []
        cur = end
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        path.reverse()

        # 路径简化：每隔几个点取一个，避免路径过密
        # 但保留起点和终点
        if len(path) > 15:
            simplified = [path[0]]
            step = len(path) // 12
            for i in range(step, len(path) - 1, step):
                simplified.append(path[i])
            simplified.append(path[-1])
            return simplified
        return path

    def load_json(self, filepath):
        """从 JSON 文件加载地图"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.name = data["地图名称"]
        self.rows = data["地图尺寸"]["行"]
        self.cols = data["地图尺寸"]["列"]
        self.grid = [["plain" for _ in range(self.cols)] for _ in range(self.rows)]

        for cell in data["地形数据"]:
            r, c = cell["行"], cell["列"]
            self.grid[r][c] = cell["地形"]

        self.player_start_zone = data.get("我方起始区域", [])
        self.enemy_zone = data.get("敌方布防区域", [])
        self.npc_positions = data.get("NPC位置", [])
        self.player_units = data.get("我方单位参考", [])
        self.enemy_units = data.get("敌方单位参考", [])
        self.victory_condition = data.get("胜利条件", self.victory_condition)
        self.turn_limit = data.get("回合限制", 20)
        self.difficulty = data.get("难度", "中等")

        print(f"[OK] 已加载地图: {self.name} ({self.rows}x{self.cols})")
        return self


# ============================================================
# 随机地图生成
# ============================================================

def generate_random_map(rows, cols, params=None):
    """随机生成一张战棋地图"""
    if params is None:
        params = {}

    water_ratio = params.get("water", 0.1)
    forest_ratio = params.get("forest", 0.15)
    mountain_ratio = params.get("mountain", 0.1)
    road_density = params.get("roads", 0.3)
    village_count = params.get("villages", 2)
    seed = params.get("seed", None)
    name = params.get("name", "随机生成地图")
    difficulty = params.get("difficulty", "中等")
    sea_width = params.get("sea_width", 0)  # 东侧海洋宽度（列数）

    if seed is not None:
        random.seed(seed)

    map_data = TacticalMap(rows, cols, name)
    map_data.difficulty = difficulty

    # 1. 初始化全平原
    for r in range(rows):
        for c in range(cols):
            map_data.grid[r][c] = "plain"

    # 1b. 东侧靠海（如有指定）
    if sea_width > 0:
        sea_start_col = max(0, cols - sea_width)
        for r in range(rows):
            for c in range(sea_start_col, cols):
                map_data.grid[r][c] = "sea"

    # 2. 随机地形分布（使用分区填充）
    terrain_types = []
    if water_ratio > 0:
        terrain_types.append(("river", water_ratio))
    if forest_ratio > 0:
        terrain_types.append(("forest", forest_ratio))
    if mountain_ratio > 0:
        terrain_types.append(("mountain", mountain_ratio))

    # 使用随机块状分布
    remaining_ratio = 1.0
    for terrain_id, ratio in terrain_types:
        terrain_ratio = ratio
        cell_count = int(rows * cols * terrain_ratio)

        # 使用随机种子生成块状区域
        placed = 0
        attempts = 0
        while placed < cell_count and attempts < 100:
            center_r = random.randint(1, rows - 2)
            center_c = random.randint(1, cols - 2)

            # 在中心附近扩展块
            block_size = random.randint(2, 5)
            for dr in range(-block_size, block_size + 1):
                for dc in range(-block_size, block_size + 1):
                    if placed >= cell_count:
                        break
                    nr, nc = center_r + dr, center_c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        # 概率随距离衰减
                        dist = abs(dr) + abs(dc)
                        prob = max(0, 1.0 - dist / (block_size * 1.5))
                        if random.random() < prob and map_data.grid[nr][nc] == "plain":
                            map_data.grid[nr][nc] = terrain_id
                            placed += 1
                if placed >= cell_count:
                    break
            attempts += 1

    # 3. 生成河流（从一侧流向另一侧）
    river_count = max(1, int(water_ratio * 3))
    for _ in range(river_count):
        _generate_river(map_data)

    # 4. 生成道路（用 A* 连接关键点）
    if road_density > 0:
        _generate_roads(map_data, road_density)

    # 5. 放置城堡和村庄
    castle_pos = _place_landmark(map_data, "castle", rows // 3, rows - 2, cols // 4, cols * 3 // 4)
    for _ in range(village_count):
        _place_landmark(map_data, "village", 1, rows - 2, 1, cols - 2)

    # 6. 海岸线生成 - 使用多级侵蚀算法制造曲折海岸线
    # 先找出所有陆地格子的距离地图，最外层变为海洋
    dist_to_edge = [[min(r, rows - 1 - r, c, cols - 1 - c) for c in range(cols)] for r in range(rows)]

    # 第1层：最外层一定为海洋
    for r in range(rows):
        for c in range(cols):
            if dist_to_edge[r][c] == 0:
                if map_data.grid[r][c] in ("plain", "road", "desert", "snow"):
                    map_data.grid[r][c] = "sea"

    # 第2层：基于随机侵蚀，从海洋向陆地不规则推进
    # 使用多个随机种子点产生海湾和半岛
    erosion_points = max(3, (rows + cols) // 3)
    for _ in range(erosion_points):
        # 从海洋边缘出发向内侵蚀
        edge_r = random.randint(0, rows - 1)
        edge_c = random.randint(0, cols - 1)
        if map_data.grid[edge_r][edge_c] != "sea":
            continue

        # 随机行走侵蚀: 从海洋边缘向陆地走, 沿途将格子变为海洋
        r, c = edge_r, edge_c
        steps = random.randint(3, max(6, (rows + cols) // 4))
        for _ in range(steps):
            # 向陆地方向随机偏移
            dr = random.choice([-1, 0, 1])
            dc = random.choice([-1, 0, 1])
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                terrain = map_data.grid[nr][nc]
                if terrain in ("plain", "road", "desert", "snow", "forest"):
                    map_data.grid[nr][nc] = "sea"
                    r, c = nr, nc
                else:
                    break
            else:
                break

    # 第3层：细胞自动机平滑 - 相邻海洋数多的陆地格子也变成海洋
    for _ in range(2):
        new_ocean = []
        for r in range(rows):
            for c in range(cols):
                if map_data.grid[r][c] in ("plain", "road", "desert", "snow", "forest"):
                    ocean_neighbors = 0
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols and map_data.grid[nr][nc] == "sea":
                            ocean_neighbors += 1
                    # 如果周围超过3个海洋邻居，且有随机性
                    if ocean_neighbors >= 3 and random.random() < 0.4:
                        new_ocean.append((r, c))
        for r, c in new_ocean:
            map_data.grid[r][c] = "sea"

    # 第4层：保护城堡/村庄/要塞周围不被海洋吞噬
    for r in range(rows):
        for c in range(cols):
            if map_data.grid[r][c] in ("castle", "village", "fort"):
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and map_data.grid[nr][nc] == "sea":
                        map_data.grid[nr][nc] = "plain"

    # 7. 玩家起始区域（底部）
    player_cols = max(3, cols // 5)
    for c in range(player_cols):
        for r in range(rows - 2, rows):
            map_data.add_player_start_zone([r, c])
            # 确保起始区域是平原
            map_data.grid[r][c] = "plain"

    # 8. 敌方布防区域（顶部，避开海洋区域）
    enemy_cols = max(3, cols // 5)
    enemy_end = cols - sea_width if sea_width > 0 else cols
    enemy_start = max(0, enemy_end - enemy_cols)
    for c in range(enemy_start, enemy_end):
        for r in range(0, 2):
            map_data.add_enemy_zone([r, c])
            map_data.grid[r][c] = "plain"

    # 9. 设置胜利条件
    if castle_pos:
        map_data.victory_condition = {
            "type": "seize",
            "target": castle_pos,
            "extra_conditions": []
        }
        # 在城堡周围放一些敌方单位参考
        castle_r, castle_c = castle_pos
        map_data.add_enemy_unit(castle_r, castle_c, "Boss", 5)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = castle_r + dr, castle_c + dc
            if 0 <= nr < rows and 0 <= nc < cols and map_data.is_passable(nr, nc):
                map_data.add_enemy_unit(nr, nc, "近卫兵", 3)
                break

    # 10. 添加我方单位参考
    for r in range(rows - 2, rows):
        for c in range(player_cols):
            if map_data.is_passable(r, c):
                unit_class = random.choice(["领主", "剑士", "战士", "弓箭手", "法师", "治疗师"])
                map_data.add_player_unit(r, c, unit_class, 1)
                break
        if len(map_data.player_units) >= 3:
            break

    # 11. 可通行验证
    _verify_connectivity(map_data)

    return map_data


def _generate_river(map_data):
    """生成河流"""
    rows, cols = map_data.rows, map_data.cols

    # 从边缘开始
    if random.random() < 0.5:
        # 水平流向
        r = random.randint(1, rows - 2)
        c = 0
        dc = 1
        max_len = random.randint(cols // 3, cols * 2 // 3)
        length = 0
        while c < cols - 1 and length < max_len:
            if map_data.grid[r][c] == "plain":
                map_data.grid[r][c] = "river"
            length += 1
            # 随机上下偏移
            if random.random() < 0.2:
                nr = r + random.choice([-1, 1])
                if 0 < nr < rows - 1:
                    r = nr
            c += dc
    else:
        # 垂直流向
        c = random.randint(1, cols - 2)
        r = 0
        dr = 1
        max_len = random.randint(rows // 3, rows * 2 // 3)
        length = 0
        while r < rows - 1 and length < max_len:
            if map_data.grid[r][c] == "plain":
                map_data.grid[r][c] = "river"
            length += 1
            if random.random() < 0.2:
                nc = c + random.choice([-1, 1])
                if 0 < nc < cols - 1:
                    c = nc
            r += dr

    # 在河流旁随机添加桥梁
    for r in range(rows):
        for c in range(cols):
            if map_data.grid[r][c] == "river":
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < rows and 0 <= nc < cols and
                            map_data.grid[nr][nc] == "plain" and
                            random.random() < 0.05):
                        map_data.grid[nr][nc] = "bridge"


def _generate_roads(map_data, density):
    """使用简单方法生成道路网络"""
    rows, cols = map_data.rows, map_data.cols
    road_count = int(rows * cols * density * 0.05)

    for _ in range(road_count):
        start_r = random.randint(0, rows - 1)
        start_c = random.randint(0, cols - 1)
        length = random.randint(3, 8)

        r, c = start_r, start_c
        for _ in range(length):
            if 0 <= r < rows and 0 <= c < cols:
                if map_data.grid[r][c] in ("plain",):
                    map_data.grid[r][c] = "road"
                # 随机方向
                direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                r += direction[0]
                c += direction[1]


def _place_landmark(map_data, terrain_id, r_min, r_max, c_min, c_max):
    """在地图范围内放置地标"""
    rows, cols = map_data.rows, map_data.cols
    r_min = max(1, r_min)
    r_max = min(rows - 2, r_max)
    c_min = max(1, c_min)
    c_max = min(cols - 2, c_max)

    for _ in range(50):
        r = random.randint(r_min, r_max)
        c = random.randint(c_min, c_max)
        if map_data.grid[r][c] == "plain":
            map_data.grid[r][c] = terrain_id

            # 在周围添加一些道路/平原保证通行
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < rows and 0 <= nc < cols and
                        map_data.grid[nr][nc] == "plain"):
                    if random.random() < 0.3:
                        map_data.grid[nr][nc] = "road"
            return [r, c]

    return None


def _verify_connectivity(map_data):
    """验证地图连通性，确保玩家起始区到目标区有路径"""
    rows, cols = map_data.rows, map_data.cols

    if not map_data.player_start_zone or not map_data.enemy_zone:
        return

    start = tuple(map_data.player_start_zone[0])
    end = tuple(map_data.enemy_zone[0])

    # BFS 寻路
    visited = set()
    queue = deque([start])
    visited.add(start)

    while queue:
        r, c = queue.popleft()
        if (r, c) == end:
            return  # 连通

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols and
                    (nr, nc) not in visited and
                    map_data.is_passable(nr, nc)):
                visited.add((nr, nc))
                queue.append((nr, nc))

    # 不连通：在中间打通一条路
    print("[!] 地图不连通，正在修复...")
    mid_r = rows // 2
    mid_c = cols // 2
    for c in range(cols):
        if map_data.is_passable(mid_r, c) or map_data.grid[mid_r][c] == "plain":
            map_data.grid[mid_r][c] = "road"
            break


# ============================================================
# 编辑功能
# ============================================================

def edit_map(json_path, edits):
    """编辑已有的地图 JSON 文件"""
    map_data = TacticalMap()
    map_data.load_json(json_path)

    for edit_cmd in edits:
        if "=" in edit_cmd:
            pos_str, terrain_id = edit_cmd.split("=", 1)
            parts = pos_str.split(",")
            if len(parts) == 2:
                r, c = int(parts[0]), int(parts[1])
                if map_data.set_terrain(r, c, terrain_id):
                    print(f"[OK] 已修改 ({r},{c}) -> {terrain_id}")
                else:
                    print(f"[!] 修改失败 ({r},{c})")

    return map_data


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="战棋地图生成工具 - 类火焰纹章风格正方形网格地图",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 随机生成地图
  python map_generator.py --rows 20 --cols 25 --random

  # 指定参数生成
  python map_generator.py --rows 15 --cols 20 --water 0.1 --forest 0.2 --mountain 0.1

  # 编辑已有地图
  python map_generator.py --edit 地图.json --terrain 3,5=forest --terrain 10,12=fort

  # 指定种子（可复现）
  python map_generator.py --rows 20 --cols 25 --random --seed 42
        """
    )

    # 地图尺寸
    parser.add_argument("--rows", type=int, default=15, help="地图行数（默认 15）")
    parser.add_argument("--cols", type=int, default=20, help="地图列数（默认 20）")
    parser.add_argument("--name", type=str, default=None, help="地图名称")

    # 随机生成参数
    parser.add_argument("--random", action="store_true", help="启用随机生成")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    parser.add_argument("--water", type=float, default=0.1, help="水域比例 0~1（默认 0.1）")
    parser.add_argument("--forest", type=float, default=0.15, help="森林比例 0~1（默认 0.15）")
    parser.add_argument("--mountain", type=float, default=0.1, help="山地比例 0~1（默认 0.1）")
    parser.add_argument("--roads", type=float, default=0.3, help="道路密度 0~1（默认 0.3）")
    parser.add_argument("--villages", type=int, default=2, help="村庄数量（默认 2）")
    parser.add_argument("--difficulty", type=str, default="中等",
                       choices=["简单", "中等", "困难"], help="难度")

    # 东侧海洋
    parser.add_argument("--sea-width", type=int, default=0,
                       help="东侧海洋宽度（列数，默认 0 表示无海洋）")

    # 编辑模式
    parser.add_argument("--edit", type=str, default=None, help="编辑已有地图 JSON 文件路径")
    parser.add_argument("--terrain", type=str, action="append",
                       help="地形修改: 行,列=地形ID（可多次使用）")

    # 胜利条件
    parser.add_argument("--objective", type=str, default="seize",
                       choices=["seize", "rout", "defend", "escape"],
                       help="胜利条件: seize(压制)/rout(全灭)/defend(防守)/escape(护送)")

    # 进攻路线
    parser.add_argument("--route", action="store_true", help="生成进攻路线参考图")

    # 输出
    parser.add_argument("--output", type=str, default=None, help="输出文件路径前缀")
    parser.add_argument("--no-png", action="store_true", help="不生成 PNG 图片")

    args = parser.parse_args()

    # 确定输出前缀
    output_prefix = args.output
    if output_prefix is None:
        name = args.name if args.name else "战棋地图"
        output_prefix = name

    # --- 编辑模式 ---
    if args.edit:
        map_data = edit_map(args.edit, args.terrain or [])
    elif args.random:
        # --- 随机生成模式 ---
        params = {
            "water": args.water,
            "forest": args.forest,
            "mountain": args.mountain,
            "roads": args.roads,
            "villages": args.villages,
            "seed": args.seed,
            "name": args.name or "随机生成地图",
            "difficulty": args.difficulty,
            "sea_width": args.sea_width,
        }
        map_data = generate_random_map(args.rows, args.cols, params)
    else:
        # --- 默认：创建空白地图 ---
        name = args.name or "空白地图"
        map_data = TacticalMap(args.rows, args.cols, name)

    # 设置胜利条件
    map_data.victory_condition["type"] = args.objective

    # 输出文件
    map_data.save_json(f"{output_prefix}.json")
    map_data.save_ascii(f"{output_prefix}.txt")
    if not args.no_png:
        map_data.save_png(f"{output_prefix}.png")
    if args.route and not args.no_png:
        map_data.save_route_map(f"{output_prefix}_路线图.png")

    # 打印 ASCII 预览
    print("\n" + "=" * 60)
    print("ASCII 预览:")
    print("=" * 60)
    print(map_data.save_ascii(None))

    print("\n" + "=" * 60)
    print(f"地图生成完成！")
    print(f"  名称: {map_data.name}")
    print(f"  尺寸: {map_data.rows}x{map_data.cols}")
    print(f"  难度: {map_data.difficulty}")
    print(f"  胜利条件: {args.objective}")
    print("=" * 60)


if __name__ == "__main__":
    main()
