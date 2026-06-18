# -*- coding: utf-8 -*-
"""快速排序算法可视化 — 全局配置常量"""

# ============================================================
# 画布尺寸
# ============================================================
WIDTH = 1920
HEIGHT = 1080
FPS = 30

# ============================================================
# 颜色方案
# ============================================================
BG_COLOR = "#1a1a2e"
BG_TOP_BAR = "#16213e"
PANEL_BG = "#0f3460"
GRID_COLOR = "#2a2a4a"

# 数组元素状态颜色
COLOR_DEFAULT = "#4a90d9"       # 默认蓝
COLOR_PIVOT = "#e74c3c"         # 基准红
COLOR_COMPARING = "#f1c40f"     # 比较中 黄
COLOR_SWAPPED = "#e67e22"       # 交换 橙
COLOR_SORTED = "#2ecc71"        # 已排序 绿
COLOR_LEFT_PART = "#3498db"     # 左分区 浅蓝
COLOR_RIGHT_PART = "#9b59b6"    # 右分区 紫
COLOR_INTRO_BAR = "#6c5ce7"     # 片头柱子颜色
COLOR_TEXT_PRIMARY = "#ffffff"
COLOR_TEXT_SECONDARY = "#b0b0c0"
COLOR_TEXT_ACCENT = "#f1c40f"

# ============================================================
# 柱状条参数
# ============================================================
BAR_WIDTH_MAX = 70          # 最大柱宽
BAR_GAP = 12                # 柱间距
BAR_MAX_HEIGHT = 500        # 最高柱子像素
BAR_BASE_Y = 780            # 柱子底部 Y 坐标
BAR_RADIUS = 8              # 圆角半径
BAR_MIN_HEIGHT = 40         # 最低柱子像素（值为0时）

# ============================================================
# 布局区域
# ============================================================
TOP_BAR_HEIGHT = 72
BOTTOM_PANEL_HEIGHT = 140
PADDING_H = 80              # 水平边距
LEGEND_X = 50
LEGEND_Y = 100
RECURSION_TREE_X = 1700
RECURSION_TREE_Y = 110

# ============================================================
# 指针 / 箭头
# ============================================================
ARROW_SIZE = 12
ARROW_OFFSET_Y = 18         # 箭头到柱底距离
LABEL_OFFSET_Y = 36         # 标签到箭头距离

# ============================================================
# 字体
# ============================================================
FONT_PATH = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD_PATH = "C:/Windows/Fonts/msyhbd.ttf"
FONT_MONO_PATH = "C:/Windows/Fonts/consola.ttf"

FONT_SIZE_TITLE = 38
FONT_SIZE_SUBTITLE = 22
FONT_SIZE_BAR_VALUE = 20
FONT_SIZE_POINTER = 16
FONT_SIZE_ANNOTATION = 26
FONT_SIZE_STEP_COUNT = 18
FONT_SIZE_LEGEND = 15
FONT_SIZE_SUMMARY = 24
FONT_SIZE_SMALL = 14

# ============================================================
# 动画时间配置（帧数 @30fps）
# ============================================================
FRAMES_TITLE = 60           # 片头停留
FRAMES_INTRO_BAR = 5        # 每根柱子出现的间隔
FRAMES_STEP_NORMAL = 18     # 普通步骤
FRAMES_STEP_SWAP = 30       # 交换步骤（更长）
FRAMES_STEP_PIVOT_PLACE = 45  # 基准归位
FRAMES_STEP_IMPORTANT = 60  # 重要步骤（选基准、递归分解等）
FRAMES_OUTRO = 90           # 片尾停留

# ============================================================
# 初始数组
# ============================================================
INITIAL_ARRAY = [6, 3, 8, 2, 9, 1, 5, 7, 4]
