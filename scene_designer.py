# -*- coding: utf-8 -*-
"""快速排序算法可视化 — 场景设计器

将 AlgorithmState 转换为视觉 SceneDefinition，
并按时间配置展开为渲染帧序列（含插值动画）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from config import *
from quicksort_logic import AlgorithmState


# ============================================================
# 视觉场景定义
# ============================================================

@dataclass
class BarDef:
    """单根柱子的视觉定义"""
    index: int          # 原始数组索引
    value: int          # 数值
    x: float            # 左上角 X
    y: float            # 左上角 Y（= BAR_BASE_Y - height）
    w: float            # 宽度
    h: float            # 高度
    color: str          # 颜色标签


@dataclass
class PointerDef:
    """指针的视觉定义"""
    x: float            # 箭头尖端 X
    y: float            # 箭头尖端 Y（柱底位置）
    label: str          # 指针标签
    color: str          # 指针颜色


@dataclass
class SceneDefinition:
    """一帧的完整视觉定义"""
    bars: list[BarDef]
    pointers: list[PointerDef]
    annotation_text: str
    current_step: int
    total_steps: int
    recursion_depth: int = 0
    left_bound: int = 0
    right_bound: int = 0
    sorted_count: int = 0


# ============================================================
# 状态 → 场景 映射
# ============================================================


def state_to_scene(
    state: AlgorithmState,
    step_index: int,
    total_steps: int,
) -> SceneDefinition:
    """将算法状态转换为视觉场景定义"""
    arr = state.array
    n = len(arr)
    max_val = max(arr) if arr else 1

    # 计算柱子布局
    bar_width = min(BAR_WIDTH_MAX, (WIDTH - 2 * PADDING_H) // n - BAR_GAP)
    total_width = n * bar_width + (n - 1) * BAR_GAP
    start_x = (WIDTH - total_width) // 2

    bars = []
    for i, val in enumerate(arr):
        x = start_x + i * (bar_width + BAR_GAP)
        height = max(BAR_MIN_HEIGHT, int((val / max_val) * BAR_MAX_HEIGHT))
        y = BAR_BASE_Y - height
        color = state.colors[i] if i < len(state.colors) else "default"
        bars.append(BarDef(
            index=i,
            value=val,
            x=float(x),
            y=float(y),
            w=float(bar_width),
            h=float(height),
            color=color,
        ))

    # 指针
    pointers = []
    bar_centers = [
        start_x + i * (bar_width + BAR_GAP) + bar_width / 2
        for i in range(n)
    ]

    # pivot 指针（上方箭头 + 标签）
    if state.pivot_index is not None and 0 <= state.pivot_index < n:
        cx = bar_centers[state.pivot_index]
        pointers.append(PointerDef(
            x=cx,
            y=BAR_BASE_Y - _bar_height(arr[state.pivot_index], max_val) - 8,
            label=f"pivot={arr[state.pivot_index]}",
            color=COLOR_PIVOT,
        ))

    # i 指针
    if state.pointer_i is not None and 0 <= state.pointer_i < n:
        cx = bar_centers[state.pointer_i]
        pointers.append(PointerDef(
            x=cx,
            y=BAR_BASE_Y + ARROW_OFFSET_Y,
            label=f"i (分区边界)",
            color=COLOR_COMPARING,
        ))

    # j 指针
    if state.pointer_j is not None and 0 <= state.pointer_j < n:
        cx = bar_centers[state.pointer_j]
        pointers.append(PointerDef(
            x=cx,
            y=BAR_BASE_Y + ARROW_OFFSET_Y + 30,
            label=f"j (扫描指针)",
            color=COLOR_LEFT_PART,
        ))

    return SceneDefinition(
        bars=bars,
        pointers=pointers,
        annotation_text=state.step_description,
        current_step=step_index + 1,
        total_steps=total_steps,
        recursion_depth=state.recursion_depth,
        left_bound=state.left_bound,
        right_bound=state.right_bound,
        sorted_count=len(state.sorted_indices),
    )


# ============================================================
# 帧展开（含插值与时间控制）
# ============================================================


def expand_scenes_to_frames(
    states: list[AlgorithmState],
) -> list[SceneDefinition]:
    """将算法状态列表展开为渲染帧序列。

    根据每步的类型分配不同的停留帧数，
    在交换步骤之间插入插值帧。
    """
    total = len(states)
    scenes: list[SceneDefinition] = []

    for i, state in enumerate(states):
        scene = state_to_scene(state, i, total)

        # 判断帧停留数
        if i == 0:
            # 初始状态：多停一会儿
            repeat = FRAMES_STEP_IMPORTANT
        elif i == total - 1:
            # 最终状态：多停
            repeat = FRAMES_STEP_IMPORTANT
        elif state.swap_pair is not None:
            # 交换步骤：插入动画
            repeat = 1
            # 插值动画帧
            prev_state = states[i - 1] if i > 0 else state
            interp_frames = _build_swap_interpolation(prev_state, state, i, total)
            scenes.extend(interp_frames)
        elif state.pivot_index is not None and i > 0:
            prev = states[i - 1]
            if prev.pivot_index != state.pivot_index:
                # 新基准选中
                repeat = FRAMES_STEP_IMPORTANT
            else:
                repeat = FRAMES_STEP_NORMAL
        elif "归位" in state.step_description:
            repeat = FRAMES_STEP_PIVOT_PLACE
        elif "递归处理" in state.step_description:
            repeat = FRAMES_STEP_IMPORTANT
        elif "排序完成" in state.step_description:
            repeat = FRAMES_STEP_IMPORTANT
        else:
            repeat = FRAMES_STEP_NORMAL

        for _ in range(repeat):
            scenes.append(scene)

    return scenes


def _build_swap_interpolation(
    state_before: AlgorithmState,
    state_swap: AlgorithmState,
    step_index: int,
    total_steps: int,
) -> list[SceneDefinition]:
    """构建交换动画的插值帧序列"""
    frames: list[SceneDefinition] = []
    arr_before = state_before.array
    arr_after = state_swap.array
    n = len(arr_before)
    max_val = max(arr_before) if arr_before else 1

    swap_pair = state_swap.swap_pair
    if swap_pair is None:
        return frames

    i_idx, j_idx = swap_pair
    if not (0 <= i_idx < n and 0 <= j_idx < n):
        return frames

    bar_width = min(BAR_WIDTH_MAX, (WIDTH - 2 * PADDING_H) // n - BAR_GAP)
    total_width = n * bar_width + (n - 1) * BAR_GAP
    start_x = (WIDTH - total_width) // 2

    def _make_bar(idx: int, val: int, color_tag: str) -> BarDef:
        x = start_x + idx * (bar_width + BAR_GAP)
        h = max(BAR_MIN_HEIGHT, int((val / max_val) * BAR_MAX_HEIGHT))
        return BarDef(
            index=idx, value=val,
            x=float(x), y=float(BAR_BASE_Y - h),
            w=float(bar_width), h=float(h),
            color=color_tag,
        )

    # 生成插值帧：两根交换的柱子移动
    interp_steps = 10
    for t in range(1, interp_steps + 1):
        alpha = t / interp_steps
        # 交换中的柱子位置插值
        bars = []
        for k in range(n):
            if k == i_idx:
                # i_idx 的柱子向右移动到 j_idx 位置
                x_i = start_x + i_idx * (bar_width + BAR_GAP)
                x_j = start_x + j_idx * (bar_width + BAR_GAP)
                cx = x_i + (x_j - x_i) * alpha
                bars.append(BarDef(
                    index=k, value=arr_before[k],
                    x=float(cx),
                    y=float(BAR_BASE_Y - max(BAR_MIN_HEIGHT, int((arr_before[k] / max_val) * BAR_MAX_HEIGHT))),
                    w=float(bar_width), h=float(max(BAR_MIN_HEIGHT, int((arr_before[k] / max_val) * BAR_MAX_HEIGHT))),
                    color="swapped",
                ))
            elif k == j_idx:
                # j_idx 的柱子向左移动到 i_idx 位置
                x_j = start_x + j_idx * (bar_width + BAR_GAP)
                x_i = start_x + i_idx * (bar_width + BAR_GAP)
                cx = x_j + (x_i - x_j) * alpha
                bars.append(BarDef(
                    index=k, value=arr_before[k],
                    x=float(cx),
                    y=float(BAR_BASE_Y - max(BAR_MIN_HEIGHT, int((arr_before[k] / max_val) * BAR_MAX_HEIGHT))),
                    w=float(bar_width), h=float(max(BAR_MIN_HEIGHT, int((arr_before[k] / max_val) * BAR_MAX_HEIGHT))),
                    color="swapped",
                ))
            else:
                bars.append(_make_bar(k, arr_before[k], state_swap.colors[k] if k < len(state_swap.colors) else "default"))

        scene = SceneDefinition(
            bars=bars,
            pointers=[],  # 交换动画中省略指针，保持画面简洁
            annotation_text=f"交换 arr[{i_idx}]={arr_before[i_idx]} 和 arr[{j_idx}]={arr_before[j_idx]} ...",
            current_step=step_index + 1,
            total_steps=total_steps,
            recursion_depth=state_swap.recursion_depth,
            left_bound=state_swap.left_bound,
            right_bound=state_swap.right_bound,
            sorted_count=len(state_swap.sorted_indices),
        )
        frames.append(scene)

    return frames


def build_intro_scenes(arr: list[int]) -> list[SceneDefinition]:
    """构建片头柱子逐个出现的场景序列"""
    n = len(arr)
    scenes = []
    for visible in range(1, n + 1):
        scene = SceneDefinition(
            bars=[],
            pointers=[],
            annotation_text=f"初始数组: {arr[:visible]}",
            current_step=0,
            total_steps=n,
        )
        scenes.append(scene)
    return scenes


def build_outro_scenes(total_steps: int) -> list[SceneDefinition]:
    """构建片尾总结场景"""
    scenes = []
    points = [
        "核心思想：分治策略 — 选基准、分区、递归",
        "每次分区将基准放到正确位置，左边 < 基准 < 右边",
        "平均时间复杂度 O(n log n)，最坏情况 O(n²)",
        "原地排序，不需要额外数组空间",
    ]
    for i, point in enumerate(points):
        scene = SceneDefinition(
            bars=[],
            pointers=[],
            annotation_text=point,
            current_step=total_steps + i + 1,
            total_steps=total_steps + len(points),
            sorted_count=total_steps,
        )
        scenes.append(scene)
    return scenes


# ============================================================
# 工具函数
# ============================================================


def _bar_height(val: int, max_val: int) -> int:
    return max(BAR_MIN_HEIGHT, int((val / max_val) * BAR_MAX_HEIGHT))
