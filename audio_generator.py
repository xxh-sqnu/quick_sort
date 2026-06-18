# -*- coding: utf-8 -*-
"""快速排序算法可视化 — 语音旁白生成器

使用 edge-tts (微软 Edge TTS) 生成中文语音旁白，
通过 pydub 按视频时间轴拼接为完整音频轨道。
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from dataclasses import dataclass
from typing import Optional

from config import FPS, FRAMES_TITLE, FRAMES_INTRO_BAR, FRAMES_STEP_IMPORTANT, FRAMES_OUTRO
from quicksort_logic import AlgorithmState


# ============================================================
# 数据结构
# ============================================================

@dataclass
class NarrationSegment:
    """一段旁白的定义"""
    text: str                           # 中文配音文本
    start_frame: int                    # 起始帧编号
    end_frame: int                      # 结束帧编号（不含）
    voice: str = "zh-CN-XiaoxiaoNeural" # TTS 发音人

    @property
    def duration_seconds(self) -> float:
        return (self.end_frame - self.start_frame) / FPS


# ============================================================
# 配音脚本构建
# ============================================================

def build_narration_script(
    states: list[AlgorithmState],
    title_frames: int,
    intro_frames: int,
    main_frames: int,
    outro_count: int,
    final_frames: int,
) -> list[NarrationSegment]:
    """根据算法阶段和帧布局生成配音脚本。

    返回按时间顺序排列的 NarrationSegment 列表。
    """
    segments: list[NarrationSegment] = []
    arr = states[0].array if states else []
    n = len(arr)

    # 帧区间边界计算
    t_end = title_frames                      # 片头结束
    i_end = t_end + intro_frames              # 数组展示结束

    # 主体算法帧索引映射：通过遍历 main_scenes 来确定关键帧位置
    # 这里使用简化策略：根据 states 数量估算帧位置
    main_start = i_end
    main_end = main_start + main_frames
    outro_start = main_end
    outro_end = outro_start + outro_count * FRAMES_STEP_IMPORTANT
    final_start = outro_end

    total_frames = final_start + final_frames

    # --- 片头 ---
    segments.append(NarrationSegment(
        text="快速排序算法原理。分治思想，原地排序，平均时间复杂度 O n log n。",
        start_frame=0,
        end_frame=t_end,
    ))

    # --- 数组展示 ---
    nums_str = "、".join(str(x) for x in arr)
    segments.append(NarrationSegment(
        text=f"这是我们要排序的数组，包含{n}个元素：{nums_str}。",
        start_frame=t_end,
        end_frame=i_end,
    ))

    # --- 主体算法：根据状态生成旁白 ---
    # 合并相邻的状态描述，减少语音片段数
    merged = _merge_states_to_narration(states)

    # 计算每个 merged 段落对应的帧范围
    # 简单按比例分配 main_frames 给各状态
    state_count = len(states)
    frame_offset = main_start
    for seg_text, state_start_idx, state_end_idx in merged:
        # 按状态数比例分配帧
        seg_frames = int(main_frames * (state_end_idx - state_start_idx + 1) / state_count)
        seg_frames = max(seg_frames, FRAMES_STEP_IMPORTANT)  # 至少 2 秒
        seg_end = min(frame_offset + seg_frames, main_end)

        if seg_end > frame_offset:
            segments.append(NarrationSegment(
                text=seg_text,
                start_frame=frame_offset,
                end_frame=seg_end,
            ))
            frame_offset = seg_end

    # --- 片尾总结 ---
    outro_texts = [
        "总结一下。快速排序的核心是分治策略：选基准、分区、递归。",
        "每次分区将基准元素放到正确的排序位置，左边元素都小于基准，右边元素都大于基准。",
        "平均时间复杂度 O n log n，最坏情况 O n 平方。它是一种原地排序算法，不需要额外数组空间。",
        "感谢观看！快速排序，优雅而高效。",
    ]
    for i, text in enumerate(outro_texts):
        start = outro_start + i * FRAMES_STEP_IMPORTANT
        end = start + FRAMES_STEP_IMPORTANT
        if start < outro_end:
            segments.append(NarrationSegment(
                text=text,
                start_frame=start,
                end_frame=min(end, outro_end),
            ))

    # --- 最终画面 ---
    segments.append(NarrationSegment(
        text="",
        start_frame=final_start,
        end_frame=total_frames,
    ))

    return segments


def _merge_states_to_narration(
    states: list[AlgorithmState],
) -> list[tuple[str, int, int]]:
    """将算法状态合并为自然的旁白段落。

    跳过重复描述，合并相同主题的连续状态。

    Returns:
        list of (narration_text, start_state_index, end_state_index)
    """
    merged: list[tuple[str, int, int]] = []

    # 关键状态分类
    key_descriptions = {
        "选择": "选择基准元素",
        "初始化": "初始化分区指针",
        "<=": "当前元素小于等于基准，交换到左边",
        ">": "当前元素大于基准，留在右边",
        "归位": "基准元素已放到正确位置",
        "递归": "递归处理左右子数组",
        "单个元素": "单个元素，自动有序",
        "排序完成": "排序完成",
    }

    i = 0
    while i < len(states):
        state = states[i]
        desc = state.step_description

        # 跳过初始状态和最终状态（单独处理）
        if i == 0 or "排序完成" in desc:
            if "排序完成" in desc:
                merged.append(("排序完成！数组已按升序排列。", i, i))
            i += 1
            continue

        # 选基准
        if "选择" in desc and "基准" in desc:
            pivot_val = state.array[state.pivot_index] if state.pivot_index is not None else "?"
            merged.append((f"选择 arr 下标 {state.pivot_index} 的值 {pivot_val} 作为基准 pivot。", i, i))
            i += 1
            continue

        # 初始化 i
        if "初始化" in desc:
            merged.append(("初始化分区边界指针 i。", i, i))
            i += 1
            continue

        # 基准归位
        if "归位" in desc:
            # 提取关键信息
            merged.append((desc.replace("，", "。"), i, i))
            i += 1
            continue

        # 递归处理
        if "递归处理" in desc:
            merged.append(("现在递归处理左右两个子数组，对每个子数组重复同样的分区过程。", i, i))
            i += 1
            continue

        # 单个元素
        if "单个元素" in desc:
            i += 1
            continue

        # 交换 / 比较 步骤：合并连续的相似状态
        if "交换" in desc or "不交换" in desc or "无需交换" in desc or "继续扫描" in desc:
            # 收集连续的扫描步骤
            scan_start = i
            swap_count = 0
            skip_count = 0
            while i < len(states):
                d = states[i].step_description
                if "交换" in d and "完成" not in d:
                    swap_count += 1
                elif "不交换" in d or "继续扫描" in d:
                    skip_count += 1
                elif "交换完成" in d:
                    pass  # skip intermediate
                else:
                    break
                i += 1

            if swap_count > 0:
                merged.append((
                    f"扫描过程中，有{swap_count}个元素小于等于基准，被交换到了左边；"
                    f"{skip_count}个元素大于基准，留在右边。",
                    scan_start, i - 1,
                ))
            else:
                i = scan_start + 1  # skip single
            continue

        i += 1

    return merged


# ============================================================
# edge-tts 语音合成
# ============================================================


async def _synthesize_one(
    text: str,
    output_path: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
    rate: str = "+10%",   # 稍快语速
) -> Optional[str]:
    """使用 edge-tts 合成单段语音。

    Returns:
        输出文件路径，失败返回 None
    """
    if not text.strip():
        # 空文本：生成极短静音
        return None

    try:
        import edge_tts
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
        )
        await communicate.save(output_path)
        return output_path
    except Exception as e:
        print(f"    TTS 合成失败 [{voice}]: {e}")
        return None


def generate_speech_files(
    segments: list[NarrationSegment],
    output_dir: str,
) -> list[tuple[int, Optional[str], float]]:
    """为每段旁白生成 MP3 语音文件。

    Returns:
        list of (segment_index, mp3_path_or_None, actual_duration_seconds)
    """
    os.makedirs(output_dir, exist_ok=True)

    async def _generate_all():
        tasks = []
        for idx, seg in enumerate(segments):
            if not seg.text.strip():
                tasks.append((idx, None, seg.duration_seconds))
            else:
                mp3_path = os.path.join(output_dir, f"seg_{idx:03d}.mp3")
                tasks.append((idx, mp3_path, seg))
        # 顺序合成以避免 API 限流
        results = []
        for idx, mp3_path, seg in tasks:
            if mp3_path is None:
                results.append((idx, None, seg))
            else:
                print(f"    合成 [{idx+1}/{len(segments)}]: {seg.text[:40]}...")
                result_path = await _synthesize_one(seg.text, mp3_path, seg.voice)
                # 获取实际时长
                duration = _get_mp3_duration(mp3_path) if result_path else seg.duration_seconds
                results.append((idx, result_path, duration))
        return results

    return asyncio.run(_generate_all())


def _get_mp3_duration(path: str) -> float:
    """用 ffprobe 获取音频文件时长（秒）"""
    try:
        import subprocess
        ffprobe_candidates = [
            os.path.join(os.path.dirname("C:/Program Files/EVCapture/ffmpeg.exe"), "ffprobe.exe"),
            "ffprobe",
            "ffprobe.exe",
        ]
        ffprobe = None
        for p in ffprobe_candidates:
            try:
                r = subprocess.run([p, "-version"], capture_output=True, timeout=3)
                if r.returncode == 0:
                    ffprobe = p
                    break
            except Exception:
                continue
        if not ffprobe:
            return 0.0

        r = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=10,
        )
        return float(r.stdout.strip())
    except Exception:
        return 0.0


# ============================================================
# 音频轨道拼接（纯 ffmpeg 实现，无需 pydub）
# ============================================================


def assemble_audio_track(
    segments: list[NarrationSegment],
    speech_results: list[tuple[int, Optional[str], float]],
    total_frames: int,
    output_path: str,
    background_music: bool = True,
) -> str:
    """用 ffmpeg concat 将分段语音拼接为完整音频轨道。

    原理：
    1. 为每个 segment 生成一段静音（时长 = slot_duration - speech_duration）
    2. 用 ffmpeg concat demuxer 将 [静音, 语音, 静音, 语音, ...] 串接
    3. 可选：叠加微弱背景环境音
    """
    import subprocess

    total_duration_s = total_frames / FPS
    speech_map = {idx: (path, dur) for idx, path, dur in speech_results}

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 查找 ffmpeg
    ffmpeg_candidates = [
        "C:/Program Files/EVCapture/ffmpeg.exe",
        "ffmpeg",
        "ffmpeg.exe",
    ]
    ffmpeg = None
    for p in ffmpeg_candidates:
        try:
            r = subprocess.run([p, "-version"], capture_output=True, timeout=3)
            if r.returncode == 0:
                ffmpeg = p
                break
        except Exception:
            continue
    if not ffmpeg:
        raise FileNotFoundError("未找到 ffmpeg")

    # 生成静音片段
    silence_dir = os.path.join(os.path.dirname(output_path), "silence")
    os.makedirs(silence_dir, exist_ok=True)

    concat_list_path = os.path.join(os.path.dirname(output_path), "concat_list.txt")
    concat_lines = []

    prev_end_s = 0.0

    for idx, seg in enumerate(segments):
        start_s = seg.start_frame / FPS
        end_s = seg.end_frame / FPS

        # 段前静音
        gap_before = start_s - prev_end_s
        if gap_before > 0.01:
            gap_file = os.path.join(silence_dir, f"gap_{idx:03d}_before.wav")
            _generate_silence_wav(gap_file, gap_before)
            concat_lines.append(f"file '{gap_file.replace(chr(92), '/')}'")

        result = speech_map.get(idx)
        if result is not None:
            mp3_path, _ = result
            if mp3_path and os.path.exists(mp3_path):
                # 语音时长
                speech_dur = _get_mp3_duration(mp3_path)
                slot_dur = seg.duration_seconds

                if speech_dur > 0 and slot_dur > 0:
                    if speech_dur > slot_dur * 1.05:
                        # 语音比槽位长，需要用 ffmpeg 加速
                        speed = speech_dur / slot_dur
                        if speed < 1.35:
                            adjusted_path = os.path.join(silence_dir, f"speed_{idx:03d}.wav")
                            _speedup_audio(mp3_path, adjusted_path, speed, ffmpeg)
                            concat_lines.append(f"file '{adjusted_path.replace(chr(92), '/')}'")
                        else:
                            concat_lines.append(f"file '{mp3_path.replace(chr(92), '/')}'")
                    else:
                        concat_lines.append(f"file '{mp3_path.replace(chr(92), '/')}'")
                else:
                    concat_lines.append(f"file '{mp3_path.replace(chr(92), '/')}'")

        # 段后静音（填充到槽位结束）
        slot_end = end_s
        if result is not None and result[0]:
            speech_dur = _get_mp3_duration(result[0])
            actual_end = start_s + min(speech_dur, seg.duration_seconds)
        else:
            actual_end = start_s

        gap_after = slot_end - max(actual_end, start_s)
        if gap_after > 0.05:
            gap_file = os.path.join(silence_dir, f"gap_{idx:03d}_after.wav")
            _generate_silence_wav(gap_file, gap_after)
            concat_lines.append(f"file '{gap_file.replace(chr(92), '/')}'")

        prev_end_s = end_s

    # 末尾静音
    if prev_end_s < total_duration_s - 0.01:
        tail_file = os.path.join(silence_dir, "tail.wav")
        _generate_silence_wav(tail_file, total_duration_s - prev_end_s)
        concat_lines.append(f"file '{tail_file.replace(chr(92), '/')}'")

    # 写入 concat 列表
    with open(concat_list_path, "w", encoding="utf-8") as f:
        f.write("\n".join(concat_lines))

    # 用 ffmpeg concat demuxer 拼接
    concat_output = os.path.join(os.path.dirname(output_path), "concat_output.wav")
    cmd = [
        ffmpeg, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c:a", "pcm_s16le",
        concat_output,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"    ffmpeg concat 失败: {r.stderr}")
        raise subprocess.CalledProcessError(r.returncode, cmd, stderr=r.stderr)

    # 可选：混入背景环境音
    if background_music:
        ambient_path = _generate_ambient_wav(
            os.path.join(os.path.dirname(output_path), "ambient.wav"),
            total_duration_s,
        )
        if ambient_path:
            mixed_output = output_path
            cmd_mix = [
                ffmpeg, "-y",
                "-i", concat_output,
                "-i", ambient_path,
                "-filter_complex",
                "[0:a]volume=1.0[a0];[1:a]volume=0.15[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2",
                "-c:a", "pcm_s16le",
                mixed_output,
            ]
            r = subprocess.run(cmd_mix, capture_output=True, text=True)
            if r.returncode == 0 and os.path.exists(mixed_output):
                print(f"  音频轨道（含背景音）: {mixed_output} ({total_duration_s:.1f}s)")
                return mixed_output

    # 直接使用拼接结果
    if concat_output != output_path:
        os.replace(concat_output, output_path)
    print(f"  音频轨道已生成: {output_path} ({total_duration_s:.1f}s)")
    return output_path


def _generate_silence_wav(path: str, duration_s: float, sample_rate: int = 44100) -> str:
    """用 ffmpeg 生成静音 WAV"""
    import subprocess
    ffmpeg = "C:/Program Files/EVCapture/ffmpeg.exe"
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r={sample_rate}:cl=mono",
        "-t", str(duration_s),
        "-c:a", "pcm_s16le",
        path,
    ]
    subprocess.run(cmd, capture_output=True, timeout=30)
    return path


def _speedup_audio(input_path: str, output_path: str, speed: float, ffmpeg: str) -> str:
    """用 ffmpeg 加速音频"""
    import subprocess
    tempo = speed
    cmd = [
        ffmpeg, "-y",
        "-i", input_path,
        "-filter:a", f"atempo={tempo:.3f}",
        "-c:a", "pcm_s16le",
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, timeout=30)
    return output_path


def _generate_ambient_wav(output_path: str, duration_s: float, sample_rate: int = 44100) -> str | None:
    """用 ffmpeg 生成柔和背景环境音"""
    try:
        import subprocess
        ffmpeg = "C:/Program Files/EVCapture/ffmpeg.exe"
        # 低频 C 和弦持续音，带淡入淡出
        cmd = [
            ffmpeg, "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency=130.81:duration={duration_s}:sample_rate={sample_rate}",
            "-f", "lavfi",
            "-i", f"sine=frequency=196:duration={duration_s}:sample_rate={sample_rate}",
            "-f", "lavfi",
            "-i", f"sine=frequency=261.63:duration={duration_s}:sample_rate={sample_rate}",
            "-filter_complex",
            (
                "[0:a]volume=0.03[a0];"
                "[1:a]volume=0.02[a1];"
                "[2:a]volume=0.015[a2];"
                "[a0][a1][a2]amix=inputs=3:duration=first[a];"
                "[a]afade=t=in:d=2,afade=t=out:st={}:d=3[aout]"
            ).format(max(0, duration_s - 3)),
            "-map", "[aout]",
            "-c:a", "pcm_s16le",
            output_path,
        ]
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        if r.returncode == 0:
            return output_path
        return None
    except Exception as e:
        print(f"    背景音生成跳过: {e}")
        return None
