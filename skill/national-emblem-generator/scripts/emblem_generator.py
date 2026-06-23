"""
国家徽标/旗帜图片生成脚本
==========================
用于将 SVG 转换为 PNG 图片，或在无法安装 cairosvg 时使用 Pillow 生成简单旗帜图片。

用法:
  # 方式1: SVG 转 PNG（需要 cairosvg）
  python emblem_generator.py svg input.svg -o output.png

  # 方式2: 直接生成简单旗帜（仅需 Pillow）
  python emblem_generator.py flag -o flag.png --colors "#FF0000" "#FFFFFF" --pattern horizontal
  python emblem_generator.py flag -o flag.png --colors "#00AA00" "#FFD700" --pattern vertical
  python emblem_generator.py flag -o flag.png --colors "#000088" "#FFFFFF" "#CC0000" --pattern tricolor

  # 方式3: 生成带中心徽标的旗帜（仅需 Pillow）
  python emblem_generator.py emblem -o emblem.png \
    --colors "#1a1a2e" "#e94560" \
    --symbol star \
    --width 800 --height 600
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# 方式1: SVG → PNG（使用 cairosvg）
# ---------------------------------------------------------------------------

def convert_svg_to_png(svg_path: str, png_path: str, scale: float = 2.0) -> bool:
    """将 SVG 文件转换为 PNG 图片（需要 cairosvg 库）"""
    try:
        import cairosvg
    except ImportError:
        print("错误: 需要安装 cairosvg 库来转换 SVG 为 PNG。")
        print("请运行: pip install cairosvg")
        print("或者使用 'flag' / 'emblem' 子命令，仅用 Pillow 生成图片。")
        return False

    if not os.path.isfile(svg_path):
        print(f"错误: 找不到 SVG 文件: {svg_path}")
        return False

    try:
        cairosvg.svg2png(url=svg_path, write_to=png_path, scale=scale)
        print(f"SVG 已成功转换为 PNG: {png_path}")
        return True
    except Exception as e:
        print(f"SVG 转换失败: {e}")
        return False


# ---------------------------------------------------------------------------
# 方式2: 使用 Pillow 生成旗帜
# ---------------------------------------------------------------------------

def _parse_color(hex_color: str) -> tuple:
    """解析 #RRGGBB 或 #RGB 格式的颜色字符串为 RGB 元组"""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _draw_stripe(draw, width: int, height: int, color: tuple,
                 offset: float, stripe_height: float):
    """绘制水平条纹"""
    y0 = int(height * offset)
    y1 = int(height * (offset + stripe_height))
    draw.rectangle([0, y0, width, y1], fill=color)


def _draw_vstripe(draw, width: int, height: int, color: tuple,
                  offset: float, stripe_width: float):
    """绘制垂直条纹"""
    x0 = int(width * offset)
    x1 = int(width * (offset + stripe_width))
    draw.rectangle([x0, 0, x1, height], fill=color)


def _draw_symbol(draw, width: int, height: int, symbol: str,
                 color: tuple, bg_color: tuple):
    """在旗帜中央绘制简易符号"""
    from PIL import ImageDraw
    cx, cy = width // 2, height // 2
    r = min(width, height) // 4  # 符号半径

    if symbol == "star":
        # 绘制五角星
        import math
        points = []
        for i in range(5):
            # 外顶点
            angle = math.radians(-90 + i * 72)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            # 内顶点
            angle = math.radians(-90 + i * 72 + 36)
            points.append((cx + r * 0.4 * math.cos(angle),
                          cy + r * 0.4 * math.sin(angle)))
        draw.polygon(points, fill=color)

    elif symbol == "circle":
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline=None)

    elif symbol == "diamond":
        points = [
            (cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)
        ]
        draw.polygon(points, fill=color)

    elif symbol == "cross":
        thickness = r // 3
        # 水平条
        draw.rectangle([cx - r, cy - thickness, cx + r, cy + thickness], fill=color)
        # 垂直条
        draw.rectangle([cx - thickness, cy - r, cx + thickness, cy + r], fill=color)

    elif symbol == "triangle":
        points = [
            (cx, cy - r),
            (cx + r, cy + r),
            (cx - r, cy + r)
        ]
        draw.polygon(points, fill=color)

    elif symbol == "moon":
        # 新月形: 画两个圆叠加
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        # 偏移切掉一部分
        from PIL import Image
        mask = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        mdraw = ImageDraw.Draw(mask)
        mdraw.ellipse([cx - r + r//3, cy - r - 5, cx + r + r//3, cy + r + 5],
                      fill=(0, 0, 0, 255))
        # 用背景色填充新月缺口
        draw.ellipse([cx - r + r//3, cy - r - 5, cx + r + r//3, cy + r + 5],
                     fill=bg_color)

    elif symbol == "sun":
        # 太阳: 中心圆 + 射线
        draw.ellipse([cx - r//2, cy - r//2, cx + r//2, cy + r//2], fill=color)
        ray_len = r
        ray_count = 12
        import math
        for i in range(ray_count):
            angle = math.radians(i * 360 / ray_count)
            x1 = cx + (r//2 + 5) * math.cos(angle)
            y1 = cy + (r//2 + 5) * math.sin(angle)
            x2 = cx + ray_len * math.cos(angle)
            y2 = cy + ray_len * math.sin(angle)
            draw.line([x1, y1, x2, y2], fill=color, width=max(2, r // 8))

    else:
        print(f"警告: 不支持的符号 '{symbol}'，使用圆形代替")
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def generate_flag(colors: list, pattern: str, width: int, height: int,
                  output_path: str) -> bool:
    """用 Pillow 生成简单旗帜图片"""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("错误: 需要安装 Pillow 库。请运行: pip install Pillow")
        return False

    if len(colors) < 1:
        print("错误: 至少需要 1 种颜色")
        return False

    rgb_colors = [_parse_color(c) for c in colors]
    img = Image.new("RGB", (width, height), rgb_colors[0])
    draw = ImageDraw.Draw(img)

    if pattern == "horizontal" and len(colors) >= 2:
        # 水平双色条纹
        _draw_stripe(draw, width, height, rgb_colors[1], 0.0, 0.5)
    elif pattern == "vertical" and len(colors) >= 2:
        # 垂直双色条纹
        _draw_vstripe(draw, width, height, rgb_colors[1], 0.0, 0.5)
    elif pattern == "tricolor" and len(colors) >= 3:
        # 三色旗（垂直三等分）
        _draw_vstripe(draw, width, height, rgb_colors[1], 0.0, 1/3)
        _draw_vstripe(draw, width, height, rgb_colors[2], 2/3, 1/3)
    elif pattern == "tricolor_h" and len(colors) >= 3:
        # 三色旗（水平三等分）
        _draw_stripe(draw, width, height, rgb_colors[1], 0.0, 1/3)
        _draw_stripe(draw, width, height, rgb_colors[2], 2/3, 1/3)
    elif pattern == "bicolor_h" and len(colors) >= 2:
        # 水平双色（各一半）
        _draw_stripe(draw, width, height, rgb_colors[1], 0.5, 0.5)
    elif pattern == "bicolor_v" and len(colors) >= 2:
        # 垂直双色（各一半）
        _draw_vstripe(draw, width, height, rgb_colors[1], 0.5, 0.5)
    elif pattern == "single":
        # 纯色，只画背景
        pass
    else:
        print(f"警告: 未知的旗帜模式 '{pattern}'，使用纯色背景")

    img.save(output_path)
    print(f"旗帜图片已生成: {output_path} ({width}x{height})")
    return True


def generate_emblem(colors: list, symbol: str, width: int, height: int,
                    output_path: str) -> bool:
    """用 Pillow 生成带中心符号的旗帜/徽标"""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("错误: 需要安装 Pillow 库。请运行: pip install Pillow")
        return False

    if len(colors) < 1:
        print("错误: 至少需要 1 种颜色")
        return False

    rgb_colors = [_parse_color(c) for c in colors]
    bg_color = rgb_colors[0]
    symbol_color = rgb_colors[1] if len(rgb_colors) > 1 else (255, 255, 255)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    _draw_symbol(draw, width, height, symbol, symbol_color, bg_color)

    img.save(output_path)
    print(f"徽标图片已生成: {output_path} ({width}x{height}), 符号: {symbol}")
    return True


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="国家徽标/旗帜图片生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # SVG → PNG（需要 cairosvg）
  python emblem_generator.py svg input.svg -o output.png --scale 2

  # 三色旗（法国风格）
  python emblem_generator.py flag -o tricolor.png \\
    --colors "#0055A4" "#FFFFFF" "#EF4135" --pattern tricolor

  # 双色旗 + 星徽（中国风格）
  python emblem_generator.py emblem -o flag.png \\
    --colors "#DE2910" "#FFDE00" --symbol star

  # 科幻风格徽标
  python emblem_generator.py emblem -o sci-fi.png \\
    --colors "#0a0a2e" "#00ffff" --symbol diamond --width 1024 --height 768
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # svg 子命令
    svg_parser = subparsers.add_parser("svg", help="将 SVG 文件转换为 PNG")
    svg_parser.add_argument("svg_file", help="输入的 SVG 文件路径")
    svg_parser.add_argument("-o", "--output", required=True, help="输出的 PNG 文件路径")
    svg_parser.add_argument("--scale", type=float, default=2.0,
                          help="输出缩放比例（默认 2.0）")

    # flag 子命令
    flag_parser = subparsers.add_parser("flag", help="生成简单旗帜图片（仅需 Pillow）")
    flag_parser.add_argument("-o", "--output", required=True, help="输出的 PNG 文件路径")
    flag_parser.add_argument("--colors", nargs="+", required=True,
                           help="颜色列表，如 #FF0000 #FFFFFF #0000FF")
    flag_parser.add_argument("--pattern", default="horizontal",
                           choices=["single", "horizontal", "vertical",
                                    "tricolor", "tricolor_h",
                                    "bicolor_h", "bicolor_v"],
                           help="旗帜条纹模式（默认 horizontal）")
    flag_parser.add_argument("--width", type=int, default=800, help="图片宽度（默认 800）")
    flag_parser.add_argument("--height", type=int, default=600, help="图片高度（默认 600）")

    # emblem 子命令
    emblem_parser = subparsers.add_parser("emblem", help="生成带中心符号的徽标（仅需 Pillow）")
    emblem_parser.add_argument("-o", "--output", required=True, help="输出的 PNG 文件路径")
    emblem_parser.add_argument("--colors", nargs="+", required=True,
                             help="颜色列表，第一个为背景色，第二个为符号色")
    emblem_parser.add_argument("--symbol", default="star",
                             choices=["star", "circle", "diamond", "cross",
                                      "triangle", "moon", "sun"],
                             help="中心符号类型（默认 star）")
    emblem_parser.add_argument("--width", type=int, default=800, help="图片宽度（默认 800）")
    emblem_parser.add_argument("--height", type=int, default=600, help="图片高度（默认 600）")

    args = parser.parse_args()

    if args.command == "svg":
        success = convert_svg_to_png(args.svg_file, args.output, args.scale)
    elif args.command == "flag":
        success = generate_flag(args.colors, args.pattern,
                               args.width, args.height, args.output)
    elif args.command == "emblem":
        success = generate_emblem(args.colors, args.symbol,
                                 args.width, args.height, args.output)
    else:
        parser.print_help()
        success = True  # 显示帮助不算失败

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
