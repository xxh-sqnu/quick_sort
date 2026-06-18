# -*- coding: utf-8 -*-
"""快速排序算法原理视频 — 主入口（含配音）

运行流程：
1. 生成算法步骤状态
2. 设计帧序列
3. 逐帧渲染 PNG
4. 编码无声 MP4
5. edge-tts 生成中文旁白 + 拼接音频
6. ffmpeg 合并视频与音频 → 最终视频
"""

import os
import sys
import time

from config import *
from quicksort_logic import quicksort_with_steps
from scene_designer import (
    state_to_scene,
    expand_scenes_to_frames,
    build_intro_scenes,
    build_outro_scenes,
    SceneDefinition,
)
from frame_renderer import (
    render_frame,
    render_title_frame,
    render_intro_array_frame,
)
from video_encoder import encode_video, encode_video_with_audio
from audio_generator import (
    build_narration_script,
    generate_speech_files,
    assemble_audio_track,
)


def main():
    print("=" * 60)
    print("  快速排序算法原理可视化视频生成器")
    print("=" * 60)

    # ================================================================
    # Step 1: 生成算法步骤
    # ================================================================
    print("\n[1/6] 运行快速排序，记录算法步骤...")
    arr = list(INITIAL_ARRAY)
    print(f"  输入数组: {arr}")
    states = quicksort_with_steps(arr)
    print(f"  共记录 {len(states)} 个算法状态")

    # ================================================================
    # Step 2: 设计帧序列
    # ================================================================
    print("\n[2/6] 设计动画帧序列...")

    total_main_steps = len(states)

    # 片头标题帧
    title_scenes = [None] * FRAMES_TITLE  # 特殊标记，渲染时处理

    # 数组逐个出现
    intro_scenes = build_intro_scenes(arr)
    intro_frames = []
    for scene in intro_scenes:
        for _ in range(FRAMES_INTRO_BAR):
            intro_frames.append(scene)

    # 主体算法动画
    main_scenes = expand_scenes_to_frames(states)

    # 片尾总结
    outro_scenes = build_outro_scenes(total_main_steps)
    outro_frames = []
    for scene in outro_scenes:
        for _ in range(FRAMES_STEP_IMPORTANT):
            outro_frames.append(scene)

    # 最终停留
    final_scene = SceneDefinition(
        bars=[],
        pointers=[],
        annotation_text="感谢观看！快速排序 — 优雅的分治算法",
        current_step=total_main_steps + len(outro_scenes) + 1,
        total_steps=total_main_steps + len(outro_scenes) + 1,
    )

    total_frames = (
        len(title_scenes) +
        len(intro_frames) +
        len(main_scenes) +
        len(outro_frames) +
        FRAMES_OUTRO
    )
    print(f"  片头: {len(title_scenes)} 帧")
    print(f"  数组展示: {len(intro_frames)} 帧")
    print(f"  算法动画: {len(main_scenes)} 帧")
    print(f"  片尾总结: {len(outro_frames)} 帧")
    print(f"  总计: {total_frames} 帧 @ {FPS}fps ≈ {total_frames // FPS} 秒")

    # ================================================================
    # Step 3: 渲染帧
    # ================================================================
    print("\n[3/6] 渲染 PNG 帧...")
    frames_dir = "output/frames"
    os.makedirs(frames_dir, exist_ok=True)

    # 清空旧帧
    for f in os.listdir(frames_dir):
        if f.endswith(".png"):
            os.remove(os.path.join(frames_dir, f))

    frame_idx = 0
    t_start = time.time()

    # 片头
    for _ in title_scenes:
        img = render_title_frame(
            "快速排序算法原理",
            "分治思想 · 原地排序 · O(n log n)",
            progress=frame_idx / len(title_scenes) if len(title_scenes) > 1 else 1.0,
        )
        img.save(os.path.join(frames_dir, f"frame_{frame_idx:04d}.png"))
        frame_idx += 1

    # 数组逐个出现
    for i, scene in enumerate(intro_frames):
        visible = (i // FRAMES_INTRO_BAR) + 1
        if visible > len(arr):
            visible = len(arr)
        img = render_intro_array_frame(
            arr, visible,
            f"准备开始排序，数组: {arr}",
            total_main_steps,
            0,
        )
        img.save(os.path.join(frames_dir, f"frame_{frame_idx:04d}.png"))
        frame_idx += 1

    # 主体算法
    for scene in main_scenes:
        img = render_frame(scene)
        img.save(os.path.join(frames_dir, f"frame_{frame_idx:04d}.png"))
        frame_idx += 1

    # 片尾
    for scene in outro_frames:
        img = render_frame(scene)
        img.save(os.path.join(frames_dir, f"frame_{frame_idx:04d}.png"))
        frame_idx += 1

    # 最终停留
    for _ in range(FRAMES_OUTRO):
        final_img = render_title_frame(
            "排序完成！",
            f"快速排序 — 分治策略的经典实现",
        )
        final_img.save(os.path.join(frames_dir, f"frame_{frame_idx:04d}.png"))
        frame_idx += 1

    elapsed = time.time() - t_start
    actual_frames = frame_idx
    print(f"  渲染完成: {actual_frames} 帧, 耗时 {elapsed:.1f}s ({actual_frames / elapsed:.1f} fps)")

    # ================================================================
    # Step 4: 编码无声视频
    # ================================================================
    print("\n[4/6] 编码无声 MP4 视频...")
    silent_video_path = "output/quicksort_silent.mp4"
    encode_video(frames_dir, silent_video_path, FPS)

    # ================================================================
    # Step 5: 生成语音旁白
    # ================================================================
    print("\n[5/6] 生成中文语音旁白...")

    narration_dir = "output/narration"
    os.makedirs(narration_dir, exist_ok=True)

    # 构建配音脚本（传入已知帧计数）
    total_title = FRAMES_TITLE
    total_intro = len(arr) * FRAMES_INTRO_BAR
    total_main = len(main_scenes)
    total_outro_count = len(outro_scenes)

    segments = build_narration_script(
        states=states,
        title_frames=total_title,
        intro_frames=total_intro,
        main_frames=total_main,
        outro_count=total_outro_count,
        final_frames=FRAMES_OUTRO,
    )

    print(f"  配音段落数: {len(segments)}")
    for i, seg in enumerate(segments):
        if seg.text.strip():
            print(f"    [{i}] 帧 {seg.start_frame}-{seg.end_frame} ({seg.duration_seconds:.1f}s): {seg.text[:50]}...")

    # TTS 合成
    print(f"  正在合成语音（使用 edge-tts）...")
    speech_results = generate_speech_files(segments, narration_dir)

    # 拼接音频轨道
    total_frames = frame_idx  # 实际渲染帧数
    audio_output = "output/audio_track.wav"
    assemble_audio_track(
        segments=segments,
        speech_results=speech_results,
        total_frames=total_frames,
        output_path=audio_output,
        background_music=True,
    )

    # ================================================================
    # Step 6: 合并视频与音频
    # ================================================================
    print("\n[6/6] 合并视频与音频...")
    output_path = "output/quicksort_with_audio.mp4"
    encode_video_with_audio(silent_video_path, audio_output, output_path)

    # ================================================================
    # 完成
    # ================================================================
    print("\n完成！")
    print(f"  无声视频: {os.path.abspath(silent_video_path)}")
    print(f"  音频轨道: {os.path.abspath(audio_output)}")
    print(f"  最终视频: {os.path.abspath(output_path)}")
    print(f"  帧文件: {os.path.abspath(frames_dir)}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
