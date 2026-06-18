# -*- coding: utf-8 -*-
"""快速排序算法可视化 — 视频编码器

调用 ffmpeg 将 PNG 帧序列合并为 MP4 视频。
"""

import subprocess
import os
import sys
from config import FPS


# 已知的 ffmpeg 路径候选
_FFMPEG_CANDIDATES = [
    "C:/Program Files/EVCapture/ffmpeg.exe",
    "ffmpeg",
    "ffmpeg.exe",
]


def _find_ffmpeg() -> str:
    """查找可用的 ffmpeg 路径"""
    for path in _FFMPEG_CANDIDATES:
        try:
            result = subprocess.run(
                [path, "-version"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    raise FileNotFoundError(
        "未找到 ffmpeg！请确保 ffmpeg 已安装并在 PATH 中。\n"
        f"已搜索: {_FFMPEG_CANDIDATES}"
    )


def encode_video(
    frames_dir: str,
    output_path: str,
    fps: int = FPS,
) -> str:
    """将 PNG 帧序列编码为 MP4 视频。

    Args:
        frames_dir: 帧 PNG 文件所在目录
        output_path: 输出 MP4 文件路径（含文件名）
        fps: 帧率

    Returns:
        输出文件的绝对路径

    Raises:
        FileNotFoundError: ffmpeg 不可用
        subprocess.CalledProcessError: 编码失败
    """
    ffmpeg = _find_ffmpeg()
    print(f"  ffmpeg: {ffmpeg}")

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 检查帧文件
    png_pattern = os.path.join(frames_dir, "frame_%04d.png")
    if not os.path.exists(frames_dir):
        raise FileNotFoundError(f"帧目录不存在: {frames_dir}")

    cmd = [
        ffmpeg,
        "-y",                          # 覆盖已存在文件
        "-framerate", str(fps),
        "-i", png_pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "23",
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",  # 确保偶数尺寸
        output_path,
    ]

    print(f"  命令: {' '.join(cmd)}")
    print(f"  正在编码 {fps}fps...")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  stderr: {result.stderr}")
        raise subprocess.CalledProcessError(
            result.returncode, cmd,
            output=result.stdout,
            stderr=result.stderr,
        )

    # 验证输出
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"编码后未找到输出文件: {output_path}")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  视频已生成: {output_path} ({size_mb:.2f} MB)")

    return os.path.abspath(output_path)


def encode_video_with_audio(
    video_path: str,
    audio_path: str,
    output_path: str,
) -> str:
    """将无声视频与音频轨道合并。

    Args:
        video_path: 已有无声 MP4 视频路径
        audio_path: 音频文件路径（WAV 格式）
        output_path: 输出带音频的 MP4 文件路径

    Returns:
        输出文件的绝对路径
    """
    ffmpeg = _find_ffmpeg()
    print(f"  ffmpeg: {ffmpeg}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    cmd = [
        ffmpeg,
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",          # 视频流直接复制（不重新编码）
        "-c:a", "aac",           # 音频编码为 AAC
        "-b:a", "192k",          # 音频比特率
        "-shortest",             # 以较短的流为准
        "-map", "0:v:0",         # 取第一个输入的视频流
        "-map", "1:a:0",         # 取第二个输入的音频流
        output_path,
    ]

    print(f"  命令: {' '.join(cmd)}")
    print(f"  正在合并视频与音频...")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  stderr: {result.stderr}")
        raise subprocess.CalledProcessError(
            result.returncode, cmd,
            output=result.stdout,
            stderr=result.stderr,
        )

    if not os.path.exists(output_path):
        raise FileNotFoundError(f"合并后未找到输出文件: {output_path}")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  带音频视频已生成: {output_path} ({size_mb:.2f} MB)")

    return os.path.abspath(output_path)


if __name__ == "__main__":
    # 独立测试
    encode_video("output/frames", "output/test.mp4")
