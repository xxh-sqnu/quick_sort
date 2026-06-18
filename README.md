# quick_sort
快速排序算法的视频讲解
## 文件结构说明
- `main.py`：程序主入口，调度所有模块，生成完整的快速排序演示视频
- `quicksort_logic.py`：快速排序算法核心逻辑，输出每一步排序的状态数据
- `frame_renderer.py`：根据排序状态逐帧渲染可视化画面
- `scene_designer.py`：视频场景样式、动画效果、配色的配置与设计
- `audio_generator.py`：生成排序演示的音效与背景音频
- `video_encoder.py`：将帧画面与音频合成，输出最终 mp4 视频
- `config.py`：全局参数配置文件，统一管理尺寸、速度、颜色等设置
- `quicksort_with_audio.mp4`：已生成的快速排序演示视频成品
