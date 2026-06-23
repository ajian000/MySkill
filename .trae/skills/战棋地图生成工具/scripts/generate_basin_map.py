"""
盆地防守战地图生成器
生成四面环山、中心城堡的 40×40 战棋防守地图。
"""
import sys
import os
import random

# 添加当前目录到路径以导入 map_generator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from map_generator import TacticalMap, _generate_river


def generate_basin_defense_map():
    """生成盆地防守地图"""
    rows, cols = 40, 40
    map_data = TacticalMap(rows, cols, "盆地防守战")
    map_data.difficulty = "中等"
    map_data.victory_condition = {
        "type": "defend",
        "target": [rows // 2, cols // 2],
        "extra_conditions": ["坚守 15 回合"]
    }
    map_data.turn_limit = 18

    center_r, center_c = rows // 2, cols // 2

    # ========== 1. 初始化全平原 ==========
    for r in range(rows):
        for c in range(cols):
            map_data.grid[r][c] = "plain"

    # ========== 2. 外圈山脉（盆地环，3格厚） ==========
    wall = 3
    for r in range(rows):
        for c in range(cols):
            if r < wall or r >= rows - wall or c < wall or c >= cols - wall:
                map_data.grid[r][c] = "mountain"

    # ========== 3. 内圈缓坡过渡（靠近山壁的部分山地） ==========
    for r in range(wall, rows - wall):
        for c in range(wall, cols - wall):
            dist_to_edge = min(r, rows - 1 - r, c, cols - 1 - c)
            if dist_to_edge <= 5 and random.random() < 0.25:
                map_data.grid[r][c] = "mountain"

    # ========== 4. 四条通道（山脉缺口） ==========
    # 上通道（正北）
    for r in range(0, 7):
        for dc in range(-2, 3):
            map_data.grid[r][center_c + dc] = "plain"
    # 下通道（正南）
    for r in range(rows - 7, rows):
        for dc in range(-2, 3):
            map_data.grid[r][center_c + dc] = "plain"
    # 左通道（正西）
    for c in range(0, 7):
        for dr in range(-2, 3):
            map_data.grid[center_r + dr][c] = "plain"
    # 右通道（正东）
    for c in range(cols - 7, cols):
        for dr in range(-2, 3):
            map_data.grid[center_r + dr][c] = "plain"

    # 通道两侧加要塞（扼守要道）
    for dr in range(-3, 4):
        for dc in [-3, 3]:
            r, c_check = center_r + dr, center_c + dc
            if 7 <= r < rows - 7 and 7 <= c_check < cols - 7:
                if map_data.grid[r][c_check] in ("plain", "mountain"):
                    map_data.grid[r][c_check] = "fort"

    # ========== 5. 十字主道路（通道 → 中心城堡） ==========
    # 纵向主干道（南北通道）
    for r in range(7, rows - 7):
        for dc in range(-2, 3):
            if map_data.grid[r][center_c + dc] in ("plain", "mountain"):
                map_data.grid[r][center_c + dc] = "road"
    # 横向主干道（东西通道）
    for c in range(7, cols - 7):
        for dr in range(-2, 3):
            if map_data.grid[center_r + dr][c] in ("plain", "mountain"):
                map_data.grid[center_r + dr][c] = "road"

    # 十字路口交点保留道路
    for dr in range(-4, 5):
        for dc in range(-4, 5):
            if map_data.grid[center_r + dr][center_c + dc] in ("mountain",):
                map_data.grid[center_r + dr][center_c + dc] = "road"

    # ========== 6. 中心城堡区域（5×5城堡防御圈） ==========
    for dr in range(-4, 5):
        for dc in range(-4, 5):
            map_data.grid[center_r + dr][center_c + dc] = "road"
    # 中心城堡
    map_data.grid[center_r][center_c] = "castle"
    # 内层四角要塞
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        map_data.grid[center_r + dr][center_c + dc] = "fort"
    # 四方向城墙（保护城堡的四个方向）
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        map_data.grid[center_r + dr][center_c + dc] = "wall"
    # 外四角要塞
    for dr, dc in [(-3, -3), (-3, 3), (3, -3), (3, 3)]:
        map_data.grid[center_r + dr][center_c + dc] = "fort"

    # ========== 7. 随机森林区域 ==========
    random.seed(42)  # 固定种子使结果可复现
    for r in range(7, rows - 7):
        for c in range(7, cols - 7):
            if map_data.grid[r][c] == "plain" and random.random() < 0.12:
                # 不在十字路上种树
                dist_to_center_c = abs(c - center_c)
                dist_to_center_r = abs(r - center_r)
                if not (dist_to_center_c <= 3 or dist_to_center_r <= 3):
                    map_data.grid[r][c] = "forest"

    # ========== 8. 随机村庄（4个） ==========
    village_positions = [
        (12, 12), (12, 28), (28, 12), (28, 28)
    ]
    for r, c in village_positions:
        if map_data.grid[r][c] == "plain":
            map_data.grid[r][c] = "village"
        else:
            # 如果被占了，找个近的平原位置
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and map_data.grid[nr][nc] == "plain":
                        map_data.grid[nr][nc] = "village"
                        break
                if map_data.grid[r][c] == "village":
                    break

    # ========== 9. 生成河流 ==========
    _generate_river(map_data)

    # 修复河流覆盖道路的问题（道路优先级高于河流）
    for r in range(7, rows - 7):
        for c in range(7, cols - 7):
            if map_data.grid[r][c] == "river":
                # 如果河流和十字路冲突，把河流改成桥梁
                dist_to_center_c = abs(c - center_c)
                dist_to_center_r = abs(r - center_r)
                if dist_to_center_c <= 3 or dist_to_center_r <= 3:
                    map_data.grid[r][c] = "bridge"

    # 清理城堡区域的河流/桥梁
    for dr in range(-4, 5):
        for dc in range(-4, 5):
            if map_data.grid[center_r + dr][center_c + dc] in ("river", "bridge"):
                map_data.grid[center_r + dr][center_c + dc] = "road"

    # ========== 10. 玩家起始区域（城堡周围，防御圈内） ==========
    for dr in range(-5, 6):
        for dc in range(-5, 6):
            r, c = center_r + dr, center_c + dc
            if 0 <= r < rows and 0 <= c < cols:
                map_data.add_player_start_zone([r, c])

    # ========== 11. 敌方布防区域（四条通道入口外侧） ==========
    # 北方
    for dc in range(-4, 5):
        for r in range(3, 7):
            map_data.add_enemy_zone([r, center_c + dc])
    # 南方
    for dc in range(-4, 5):
        for r in range(rows - 7, rows - 3):
            map_data.add_enemy_zone([r, center_c + dc])
    # 西方
    for dr in range(-4, 5):
        for c in range(3, 7):
            map_data.add_enemy_zone([center_r + dr, c])
    # 东方
    for dr in range(-4, 5):
        for c in range(cols - 7, cols - 3):
            map_data.add_enemy_zone([center_r + dr, c])

    # ========== 12. 我方单位参考 ==========
    map_data.add_player_unit(center_r, center_c, "领主", 3)
    map_data.add_player_unit(center_r - 3, center_c - 1, "剑士", 2)
    map_data.add_player_unit(center_r - 3, center_c + 1, "弓箭手", 2)
    map_data.add_player_unit(center_r + 3, center_c - 1, "法师", 2)
    map_data.add_player_unit(center_r + 3, center_c + 1, "治疗师", 2)
    map_data.add_player_unit(center_r, center_c - 4, "重甲兵", 2)
    map_data.add_player_unit(center_r, center_c + 4, "重甲兵", 2)

    # ========== 13. 敌方单位参考（四路进攻集群） ==========
    # 北方进攻
    map_data.add_enemy_unit(4, center_c, "Boss·北方将领", 5)
    map_data.add_enemy_unit(5, center_c - 2, "剑兵", 3)
    map_data.add_enemy_unit(5, center_c + 2, "枪兵", 3)
    map_data.add_enemy_unit(5, center_c, "弓箭手", 3)
    # 南方进攻
    map_data.add_enemy_unit(rows - 5, center_c, "勇士·南方统领", 4)
    map_data.add_enemy_unit(rows - 6, center_c - 2, "剑兵", 3)
    map_data.add_enemy_unit(rows - 6, center_c + 2, "弓骑兵", 3)
    # 西方进攻
    map_data.add_enemy_unit(center_r, 4, "暗杀者·西部刺客", 4)
    map_data.add_enemy_unit(center_r - 2, 5, "剑兵", 3)
    map_data.add_enemy_unit(center_r + 2, 5, "法师", 3)
    # 东方进攻
    map_data.add_enemy_unit(center_r, cols - 5, "骑士·东部骑兵长", 4)
    map_data.add_enemy_unit(center_r - 2, cols - 6, "骑兵", 3)
    map_data.add_enemy_unit(center_r + 2, cols - 6, "骑兵", 3)

    # 增加一些散兵游勇在森林区域
    for _ in range(6):
        for attempt in range(30):
            r = random.randint(8, rows - 8)
            c = random.randint(8, cols - 8)
            if map_data.grid[r][c] == "forest":
                map_data.add_enemy_unit(r, c, "伏兵", 2)
                break

    return map_data


if __name__ == "__main__":
    map_data = generate_basin_defense_map()

    # 输出到 MySkill 目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.join(script_dir, "..", "..", "..", "..")
    output_dir = os.path.join(project_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)

    output_prefix = os.path.join(output_dir, "盆地防守战")

    map_data.save_json(f"{output_prefix}.json")
    map_data.save_ascii(f"{output_prefix}.txt")
    map_data.save_png(f"{output_prefix}.png")
    map_data.save_route_map(f"{output_prefix}_路线图.png")

    print("\n" + "=" * 60)
    print("ASCII 预览:")
    print("=" * 60)
    ascii_map = map_data.save_ascii(None)
    print(ascii_map)

    print("\n" + "=" * 60)
    print("盆地防守战地图生成完成！")
    print(f"  名称: {map_data.name}")
    print(f"  尺寸: {map_data.rows}x{map_data.cols}")
    print(f"  难度: {map_data.difficulty}")
    print(f"  胜利条件: 防守 - 坚守 15 回合")
    print(f"  回合限制: {map_data.turn_limit}")
    print("=" * 60)
    print(f"\n输出文件:")
    print(f"  {output_prefix}.json")
    print(f"  {output_prefix}.txt")
    print(f"  {output_prefix}.png")
    print(f"  {output_prefix}_路线图.png")
