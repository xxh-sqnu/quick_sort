# -*- coding: utf-8 -*-
"""快速排序算法 — 逐步状态记录

quicksort_with_steps(arr) 不直接排序，而是模拟排序过程，
将每一步的中间状态记录为 AlgorithmState 列表。
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AlgorithmState:
    """快速排序某一步的完整状态快照"""
    array: list[int]                        # 当前数组值
    colors: list[str]                       # 每个元素的颜色标签
    pivot_index: Optional[int] = None       # 当前基准元素索引
    pointer_i: Optional[int] = None         # 分区边界指针 i
    pointer_j: Optional[int] = None         # 扫描指针 j
    step_description: str = ""              # 中文步骤说明
    recursion_depth: int = 0                # 递归深度
    left_bound: int = 0                     # 当前子数组左边界
    right_bound: int = 0                    # 当前子数组右边界
    sorted_indices: set = field(default_factory=set)  # 已排好序的索引集合
    swap_pair: Optional[tuple[int, int]] = None  # 正在交换的两个索引（用于动画）


def quicksort_with_steps(arr: list[int]) -> list[AlgorithmState]:
    """对 arr 执行快速排序，返回所有步骤的 AlgorithmState 列表。

    返回的列表包含从初始状态到完全排序的每一步。
    初始数组不会被修改（在副本上操作）。
    """
    states: list[AlgorithmState] = []
    arr_copy = list(arr)
    n = len(arr_copy)
    sorted_set: set[int] = set()

    # 初始状态
    states.append(AlgorithmState(
        array=list(arr_copy),
        colors=["default"] * n,
        step_description=f"初始数组: {arr_copy}",
        recursion_depth=0,
        left_bound=0,
        right_bound=n - 1,
        sorted_indices=set(),
    ))

    _quicksort(arr_copy, 0, n - 1, 0, states, sorted_set)

    # 最终状态：全部排序完成
    states.append(AlgorithmState(
        array=list(arr_copy),
        colors=["sorted"] * n,
        pivot_index=None,
        pointer_i=None,
        pointer_j=None,
        step_description="排序完成！数组已按升序排列 ✓",
        recursion_depth=0,
        left_bound=0,
        right_bound=n - 1,
        sorted_indices=set(range(n)),
    ))

    return states


def _quicksort(
    arr: list[int],
    left: int,
    right: int,
    depth: int,
    states: list[AlgorithmState],
    sorted_set: set[int],
) -> None:
    """递归快速排序，每一步记录状态"""
    if left >= right:
        # 单个元素或空区间，标记为已排序
        if left == right:
            sorted_set.add(left)
            colors = _build_colors(arr, states[0].array, sorted_set, None, None, None)
            states.append(AlgorithmState(
                array=list(arr),
                colors=colors,
                pivot_index=None,
                pointer_i=None,
                pointer_j=None,
                step_description=f"单个元素 arr[{left}]={arr[left]}，自动有序",
                recursion_depth=depth,
                left_bound=left,
                right_bound=right,
                sorted_indices=set(sorted_set),
            ))
        return

    # --- 第1步：选择基准 ---
    pivot_idx = right
    pivot_val = arr[pivot_idx]
    colors = _build_colors(arr, states[0].array, sorted_set, pivot_idx, None, None)
    states.append(AlgorithmState(
        array=list(arr),
        colors=colors,
        pivot_index=pivot_idx,
        pointer_i=None,
        pointer_j=None,
        step_description=f"选择 arr[{pivot_idx}]={pivot_val} 作为基准（pivot）",
        recursion_depth=depth,
        left_bound=left,
        right_bound=right,
        sorted_indices=set(sorted_set),
    ))

    # --- 第2步：初始化 i 指针 ---
    i = left - 1
    colors = _build_colors(arr, states[0].array, sorted_set, pivot_idx, i, None)
    states.append(AlgorithmState(
        array=list(arr),
        colors=colors,
        pivot_index=pivot_idx,
        pointer_i=i if i >= left else None,
        pointer_j=None,
        step_description=f"初始化分区边界 i = {i}（{i+1-left} 个元素小于基准）",
        recursion_depth=depth,
        left_bound=left,
        right_bound=right,
        sorted_indices=set(sorted_set),
    ))

    # --- 第3步：扫描分区 ---
    for j in range(left, right):
        # 比较 arr[j] 与 pivot
        colors = _build_colors(arr, states[0].array, sorted_set, pivot_idx, i, j)
        if arr[j] <= pivot_val:
            # 小于等于基准 → i++ 并交换
            i += 1
            if i != j:
                # 记录交换前状态
                states.append(AlgorithmState(
                    array=list(arr),
                    colors=_build_colors(arr, states[0].array, sorted_set, pivot_idx, i, j,
                                         highlight_swap=[i, j]),
                    pivot_index=pivot_idx,
                    pointer_i=i,
                    pointer_j=j,
                    step_description=f"arr[{j}]={arr[j]} <= {pivot_val}，交换 arr[{i}] 和 arr[{j}]",
                    recursion_depth=depth,
                    left_bound=left,
                    right_bound=right,
                    sorted_indices=set(sorted_set),
                    swap_pair=(i, j),
                ))
                arr[i], arr[j] = arr[j], arr[i]
                # 交换后状态
                states.append(AlgorithmState(
                    array=list(arr),
                    colors=_build_colors(arr, states[0].array, sorted_set, pivot_idx, i, j),
                    pivot_index=pivot_idx,
                    pointer_i=i,
                    pointer_j=j,
                    step_description=f"交换完成：arr[{i}]={arr[i]}, arr[{j}]={arr[j]}",
                    recursion_depth=depth,
                    left_bound=left,
                    right_bound=right,
                    sorted_indices=set(sorted_set),
                ))
            else:
                # i == j，不需要交换
                states.append(AlgorithmState(
                    array=list(arr),
                    colors=colors,
                    pivot_index=pivot_idx,
                    pointer_i=i,
                    pointer_j=j,
                    step_description=f"arr[{j}]={arr[j]} <= {pivot_val}，i 移动到 {i}（无需交换）",
                    recursion_depth=depth,
                    left_bound=left,
                    right_bound=right,
                    sorted_indices=set(sorted_set),
                ))
        else:
            # 大于基准，不交换
            states.append(AlgorithmState(
                array=list(arr),
                colors=colors,
                pivot_index=pivot_idx,
                pointer_i=i if i >= left else None,
                pointer_j=j,
                step_description=f"arr[{j}]={arr[j]} > {pivot_val}，不交换，继续扫描",
                recursion_depth=depth,
                left_bound=left,
                right_bound=right,
                sorted_indices=set(sorted_set),
            ))

    # --- 第4步：基准归位 ---
    pivot_final = i + 1
    if pivot_final != pivot_idx:
        arr[pivot_final], arr[pivot_idx] = arr[pivot_idx], arr[pivot_final]
    sorted_set.add(pivot_final)
    colors = _build_colors(arr, states[0].array, sorted_set, None, None, None)
    states.append(AlgorithmState(
        array=list(arr),
        colors=colors,
        pivot_index=None,
        pointer_i=None,
        pointer_j=None,
        step_description=f"基准 {pivot_val} 归位到 arr[{pivot_final}]，左边元素全小于它，右边全大于它",
        recursion_depth=depth,
        left_bound=left,
        right_bound=right,
        sorted_indices=set(sorted_set),
    ))

    # --- 第5步：递归分解 ---
    if left <= pivot_final - 1 and pivot_final + 1 <= right:
        # 两边都有子数组
        colors = _build_colors(arr, states[0].array, sorted_set, None, None, None,
                               left_part=(left, pivot_final - 1),
                               right_part=(pivot_final + 1, right))
        states.append(AlgorithmState(
            array=list(arr),
            colors=colors,
            pivot_index=None,
            pointer_i=None,
            pointer_j=None,
            step_description=f"递归处理：左子数组 [{left}..{pivot_final-1}] 和 右子数组 [{pivot_final+1}..{right}]",
            recursion_depth=depth,
            left_bound=left,
            right_bound=right,
            sorted_indices=set(sorted_set),
        ))

    # 递归左子数组
    _quicksort(arr, left, pivot_final - 1, depth + 1, states, sorted_set)
    # 递归右子数组
    _quicksort(arr, pivot_final + 1, right, depth + 1, states, sorted_set)


def _build_colors(
    arr: list[int],
    original: list[int],
    sorted_set: set[int],
    pivot_idx: Optional[int],
    i: Optional[int],
    j: Optional[int],
    highlight_swap: Optional[list[int]] = None,
    left_part: Optional[tuple[int, int]] = None,
    right_part: Optional[tuple[int, int]] = None,
) -> list[str]:
    """根据当前状态构建颜色列表"""
    n = len(arr)
    colors = ["default"] * n

    # 已排序元素
    for idx in sorted_set:
        if 0 <= idx < n:
            colors[idx] = "sorted"

    # 高亮交换对（优先级最高）
    if highlight_swap:
        for idx in highlight_swap:
            if 0 <= idx < n:
                colors[idx] = "swapped"
        return colors

    # 基准
    if pivot_idx is not None and 0 <= pivot_idx < n:
        if pivot_idx not in sorted_set:
            colors[pivot_idx] = "pivot"

    # 比较中的元素 j
    if j is not None and 0 <= j < n:
        if j not in sorted_set and j != pivot_idx:
            colors[j] = "comparing"

    # 高亮左/右分区
    if left_part:
        l, r = left_part
        for idx in range(l, r + 1):
            if idx not in sorted_set:
                colors[idx] = "left_part"
    if right_part:
        l, r = right_part
        for idx in range(l, r + 1):
            if idx not in sorted_set:
                colors[idx] = "right_part"

    return colors
