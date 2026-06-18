# -*- coding: utf-8 -*-
"""快速排序算法可视化 — Pillow 帧渲染引擎

将 SceneDefinition 渲染为 1920x1080 的 PIL Image。
"""

from __future__ import annotations

import math
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from config import *
from scene_designer import SceneDefinition, BarDef, PointerDef


# ============================================================
# 字体加载（延迟加载，全局缓存）
# ============================================================
_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _get_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in _font_cache:
        try:
            _font_cache[key] = ImageFont.truetype(path, size)
        except (OSError, IOError):
            # 回退到默认字体
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD_PATH if bold else FONT_PATH
    return _get_font(path, size)


def _font_mono(size: int) -> ImageFont.FreeTypeFont:
    return _get_font(FONT_MONO_PATH, size)


# ============================================================
# 颜色映射
# ============================================================
COLOR_MAP = {
    "default": COLOR_DEFAULT,
    "pivot": COLOR_PIVOT,
    "comparing": COLOR_COMPARING,
    "swapped": COLOR_SWAPPED,
    "sorted": COLOR_SORTED,
    "left_part": COLOR_LEFT_PART,
    "right_part": COLOR_RIGHT_PART,
    "intro": COLOR_INTRO_BAR,
}


def _bar_color(color_tag: str) -> str:
    return COLOR_MAP.get(color_tag, COLOR_DEFAULT)


# ============================================================
# 绘制工具函数
# ============================================================


def _draw_rounded_rect(
    draw: ImageDraw.Draw,
    x1: float, y1: float, x2: float, y2: float,
    radius: float,
    fill: str,
) -> None:
    """绘制圆角矩形"""
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    r = int(radius)
    # 主体矩形
    draw.rectangle([x1 + r, y1, x2 - r, y2], fill=fill)
    draw.rectangle([x1, y1 + r, x2, y2 - r], fill=fill)
    # 四个角
    draw.pieslice([x1, y1, x1 + 2 * r, y1 + 2 * r], 180, 270, fill=fill)
    draw.pieslice([x2 - 2 * r, y1, x2, y1 + 2 * r], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - 2 * r, x1 + 2 * r, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - 2 * r, y2 - 2 * r, x2, y2], 0, 90, fill=fill)


def _draw_arrow_down(
    draw: ImageDraw.Draw,
    cx: float, cy: float,
    size: int,
    fill: str,
) -> None:
    """在 (cx, cy) 绘制向下的三角箭头"""
    points = [
        (cx, cy + size),
        (cx - size, cy - size // 2),
        (cx + size, cy - size // 2),
    ]
    draw.polygon([(int(x), int(y)) for x, y in points], fill=fill)


def _draw_arrow_up(
    draw: ImageDraw.Draw,
    cx: float, cy: float,
    size: int,
    fill: str,
) -> None:
    """在 (cx, cy) 绘制向上的三角箭头"""
    points = [
        (cx, cy - size),
        (cx - size, cy + size // 2),
        (cx + size, cy + size // 2),
    ]
    draw.polygon([(int(x), int(y)) for x, y in points], fill=fill)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """#rrggbb → (r, g, b)"""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ============================================================
# 主渲染函数
# ============================================================


def render_frame(scene: SceneDefinition) -> Image.Image:
    """将 SceneDefinition 渲染为一张 PIL Image"""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    _draw_background(draw)
    _draw_top_bar(draw)
    _draw_bars(draw, scene)
    _draw_pointers(draw, scene)
    _draw_annotation_panel(draw, scene)
    _draw_step_counter(draw, scene)
    _draw_legend(draw)
    _draw_recursion_context(draw, scene)

    return img


def render_title_frame(title: str, subtitle: str, progress: float = 0.0) -> Image.Image:
    """渲染片头/片尾帧（无柱子，纯文字）"""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # 背景装饰：渐变圆
    for i in range(3):
        r = 200 + i * 100
        alpha = 30 - i * 8
        cx, cy = WIDTH // 2, HEIGHT // 2 - 50
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline=_hex_to_rgb(COLOR_LEFT_PART) + (alpha,),
            width=2,
        )

    # 标题
    title_font = _font(56, bold=True)
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(
        ((WIDTH - tw) // 2, HEIGHT // 2 - 100),
        title,
        fill=COLOR_TEXT_PRIMARY,
        font=title_font,
    )

    # 副标题
    sub_font = _font(28)
    bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    sw = bbox[2] - bbox[0]
    draw.text(
        ((WIDTH - sw) // 2, HEIGHT // 2 + 10),
        subtitle,
        fill=COLOR_TEXT_SECONDARY,
        font=sub_font,
    )

    # 进度指示
    if 0 < progress < 1:
        _draw_progress_bar(draw, WIDTH // 4, HEIGHT - 160, WIDTH // 2, 4, progress)

    return img


def render_intro_array_frame(
    arr: list[int],
    visible_count: int,
    step_text: str,
    total_steps: int,
    current_step: int,
) -> Image.Image:
    """渲染片头数组逐个出现的过渡帧"""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    _draw_background(draw)
    _draw_top_bar(draw)

    # 柱子逐渐出现
    n = len(arr)
    max_val = max(arr)
    bar_width = min(BAR_WIDTH_MAX, (WIDTH - 2 * PADDING_H) // n - BAR_GAP)
    total_width = n * bar_width + (n - 1) * BAR_GAP
    start_x = (WIDTH - total_width) // 2

    for i in range(visible_count):
        x = start_x + i * (bar_width + BAR_GAP)
        height = max(BAR_MIN_HEIGHT, int((arr[i] / max_val) * BAR_MAX_HEIGHT))
        y = BAR_BASE_Y - height
        color = COLOR_INTRO_BAR
        _draw_rounded_rect(draw, x, y, x + bar_width, BAR_BASE_Y, BAR_RADIUS, color)
        # 数值标签
        val_text = str(arr[i])
        val_font = _font(FONT_SIZE_BAR_VALUE, bold=True)
        bbox = draw.textbbox((0, 0), val_text, font=val_font)
        tw = bbox[2] - bbox[0]
        draw.text(
            (x + (bar_width - tw) // 2, y - 28),
            val_text,
            fill=COLOR_TEXT_PRIMARY,
            font=val_font,
        )

    # 说明文字
    _draw_annotation_panel(draw, SceneDefinition(
        bars=[],
        pointers=[],
        annotation_text=step_text,
        current_step=current_step,
        total_steps=total_steps,
        recursion_depth=0,
        left_bound=0,
        right_bound=len(arr) - 1,
        sorted_count=0,
    ))
    _draw_step_counter_raw(draw, current_step, total_steps)
    _draw_legend(draw)

    return img


# ============================================================
# 内部绘制函数
# ============================================================


def _draw_background(draw: ImageDraw.Draw) -> None:
    """绘制背景网格"""
    # 垂直网格线
    grid_spacing = 80
    for x in range(0, WIDTH, grid_spacing):
        draw.line([(x, TOP_BAR_HEIGHT), (x, HEIGHT)], fill=GRID_COLOR, width=1)
    # 水平网格线
    for y in range(TOP_BAR_HEIGHT, HEIGHT, grid_spacing):
        draw.line([(0, y), (WIDTH, y)], fill=GRID_COLOR, width=1)


def _draw_top_bar(draw: ImageDraw.Draw) -> None:
    """绘制顶部标题栏"""
    draw.rectangle([(0, 0), (WIDTH, TOP_BAR_HEIGHT)], fill=BG_TOP_BAR)
    # 标题
    title_font = _font(FONT_SIZE_TITLE, bold=True)
    draw.text(
        (40, (TOP_BAR_HEIGHT - FONT_SIZE_TITLE) // 2 - 2),
        "快速排序 (Quicksort) 算法原理可视化",
        fill=COLOR_TEXT_PRIMARY,
        font=title_font,
    )
    # 底部装饰线
    for i in range(3):
        y = TOP_BAR_HEIGHT - 3 + i
        alpha = 200 - i * 60
        r, g, b = _hex_to_rgb(COLOR_PIVOT)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, alpha), width=1)


def _draw_bars(draw: ImageDraw.Draw, scene: SceneDefinition) -> None:
    """绘制数组柱状条"""
    bars = scene.bars
    if not bars:
        return

    for bar in bars:
        x, y, w, h = bar.x, bar.y, bar.w, bar.h
        color = _bar_color(bar.color)

        # 高亮交换中的柱子：额外描边
        if bar.color == "swapped":
            _draw_rounded_rect(draw, x - 3, y - 3, x + w + 3, BAR_BASE_Y + 3, BAR_RADIUS + 2, COLOR_SWAPPED)
            # 调亮主色
            _draw_rounded_rect(draw, x, y, x + w, BAR_BASE_Y, BAR_RADIUS, "#ff9f43")
        elif bar.color == "pivot":
            _draw_rounded_rect(draw, x - 2, y - 2, x + w + 2, BAR_BASE_Y + 2, BAR_RADIUS + 1, COLOR_PIVOT)
            _draw_rounded_rect(draw, x, y, x + w, BAR_BASE_Y, BAR_RADIUS, color)
        else:
            _draw_rounded_rect(draw, x, y, x + w, BAR_BASE_Y, BAR_RADIUS, color)

        # 数值标签
        val_text = str(bar.value)
        val_font = _font(FONT_SIZE_BAR_VALUE, bold=True)
        bbox = draw.textbbox((0, 0), val_text, font=val_font)
        tw = bbox[2] - bbox[0]
        draw.text(
            (x + (w - tw) // 2, y - 30),
            val_text,
            fill=COLOR_TEXT_PRIMARY,
            font=val_font,
        )

        # 索引标签（柱子下方）
        idx_text = str(bar.index)
        idx_font = _font(FONT_SIZE_SMALL)
        bbox = draw.textbbox((0, 0), idx_text, font=idx_font)
        iw = bbox[2] - bbox[0]
        draw.text(
            (x + (w - iw) // 2, BAR_BASE_Y + 6),
            idx_text,
            fill=COLOR_TEXT_SECONDARY,
            font=idx_font,
        )


def _draw_pointers(draw: ImageDraw.Draw, scene: SceneDefinition) -> None:
    """绘制指针箭头和标签"""
    for ptr in scene.pointers:
        _draw_arrow_down(draw, ptr.x, ptr.y, ARROW_SIZE, ptr.color)
        # 标签
        label_font = _font(FONT_SIZE_POINTER, bold=True)
        bbox = draw.textbbox((0, 0), ptr.label, font=label_font)
        lw = bbox[2] - bbox[0]
        draw.text(
            (ptr.x - lw // 2, ptr.y + LABEL_OFFSET_Y),
            ptr.label,
            fill=ptr.color,
            font=label_font,
        )


def _draw_annotation_panel(draw: ImageDraw.Draw, scene: SceneDefinition) -> None:
    """绘制底部注释面板"""
    panel_y = HEIGHT - BOTTOM_PANEL_HEIGHT
    draw.rectangle([(0, panel_y), (WIDTH, HEIGHT)], fill=PANEL_BG)
    # 顶部装饰线
    draw.line([(0, panel_y), (WIDTH, panel_y)], fill=COLOR_PIVOT, width=3)

    # 步骤图标
    icon_size = 32
    icon_x = 60
    icon_y = panel_y + (BOTTOM_PANEL_HEIGHT - icon_size) // 2
    draw.ellipse(
        [icon_x, icon_y, icon_x + icon_size, icon_y + icon_size],
        fill=COLOR_PIVOT,
    )
    step_icon_font = _font(18, bold=True)
    draw.text(
        (icon_x + 10, icon_y + 4),
        "▶",
        fill=COLOR_TEXT_PRIMARY,
        font=step_icon_font,
    )

    # 主说明文字
    text = scene.annotation_text
    text_font = _font(FONT_SIZE_ANNOTATION)
    # 文字自动换行
    max_text_width = WIDTH - 400
    lines = _wrap_text(draw, text, text_font, max_text_width)
    line_height = FONT_SIZE_ANNOTATION + 8
    start_y = panel_y + (BOTTOM_PANEL_HEIGHT - len(lines) * line_height) // 2
    for i, line in enumerate(lines):
        draw.text(
            (120, start_y + i * line_height),
            line,
            fill=COLOR_TEXT_PRIMARY,
            font=text_font,
        )


def _draw_step_counter(draw: ImageDraw.Draw, scene: SceneDefinition) -> None:
    """绘制步骤计数器"""
    _draw_step_counter_raw(draw, scene.current_step, scene.total_steps)


def _draw_step_counter_raw(draw: ImageDraw.Draw, current: int, total: int) -> None:
    """绘制步骤计数器（无 scene 对象时使用）"""
    text = f"步骤 {current} / {total}"
    text_font = _font(FONT_SIZE_STEP_COUNT)
    bbox = draw.textbbox((0, 0), text, font=text_font)
    tw = bbox[2] - bbox[0]
    x = WIDTH - tw - 60
    y = TOP_BAR_HEIGHT + 20
    draw.text((x, y), text, fill=COLOR_TEXT_SECONDARY, font=text_font)

    # 进度条
    bar_x = WIDTH - 260
    bar_w = 200
    bar_y = y + 28
    bar_h = 4
    progress = current / total if total > 0 else 0
    _draw_progress_bar(draw, bar_x, bar_y, bar_w, bar_h, progress)


def _draw_progress_bar(
    draw: ImageDraw.Draw,
    x: int, y: int, w: int, h: int,
    progress: float,
) -> None:
    """绘制水平进度条"""
    draw.rectangle([(x, y), (x + w, y + h)], fill=GRID_COLOR)
    fill_w = int(w * progress)
    if fill_w > 0:
        draw.rectangle([(x, y), (x + fill_w, y + h)], fill=COLOR_SORTED)


def _draw_legend(draw: ImageDraw.Draw) -> None:
    """绘制左上角颜色图例"""
    items = [
        ("默认", COLOR_DEFAULT),
        ("基准", COLOR_PIVOT),
        ("比较中", COLOR_COMPARING),
        ("交换", COLOR_SWAPPED),
        ("已排序", COLOR_SORTED),
        ("左分区", COLOR_LEFT_PART),
        ("右分区", COLOR_RIGHT_PART),
    ]
    x, y = LEGEND_X, LEGEND_Y
    box_size = 14
    gap = 22

    # 标题
    legend_title = _font(FONT_SIZE_LEGEND, bold=True)
    draw.text((x, y - 22), "图例", fill=COLOR_TEXT_SECONDARY, font=legend_title)

    for i, (label, color) in enumerate(items):
        iy = y + i * gap
        draw.rectangle([(x, iy), (x + box_size, iy + box_size)], fill=color)
        label_font = _font(FONT_SIZE_SMALL)
        draw.text(
            (x + box_size + 8, iy - 1),
            label,
            fill=COLOR_TEXT_SECONDARY,
            font=label_font,
        )


def _draw_recursion_context(draw: ImageDraw.Draw, scene: SceneDefinition) -> None:
    """绘制右上角递归上下文信息"""
    x = RECURSION_TREE_X - 150
    y = RECURSION_TREE_Y

    info_font = _font(FONT_SIZE_SMALL)
    depth_text = f"递归深度: {scene.recursion_depth}"
    range_text = f"当前区间: [{scene.left_bound}, {scene.right_bound}]"
    sorted_text = f"已排序: {scene.sorted_count} / {scene.total_steps}"

    lines = [depth_text, range_text]
    if scene.sorted_count > 0:
        lines.append(sorted_text)

    for i, line in enumerate(lines):
        draw.text((x, y + i * 22), line, fill=COLOR_TEXT_SECONDARY, font=info_font)


def _wrap_text(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """将文本按最大宽度自动换行"""
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
    return lines if lines else [text]
