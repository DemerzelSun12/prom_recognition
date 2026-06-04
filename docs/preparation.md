# Preparation Notes

## Image And Video Data

建议固定游戏窗口为 2048 x 1080，并使用 PNG 截图或短视频采样。

需要准备的数据：

- 无圆圈背景图：10-20 张。
- 单个圆圈截图：30-50 张。
- 圆圈不同收缩阶段：至少 10 组，每组 5-10 帧。
- 多圆圈同时出现：20-40 张。
- 不同歌曲或难度：每类 20 张以上。
- 复杂特效或遮挡场景：20 张左右。
- 点击判定瞬间截图：10-20 张。

## Recommended Capture Rules

- 只截游戏窗口，不截整个桌面。
- Windows 缩放建议为 100%。
- macOS 需要给 Terminal 或 VS Code 开启 Screen Recording 权限。
- 截图格式使用 PNG。
- 文件名尽量表达场景类型，例如 `single_circle_001.png`。

## Development Order

1. 从静态截图中识别圆圈。
2. 从视频逐帧识别圆圈。
3. 加入多帧轨迹跟踪。
4. 估计收缩速度和触发时间。
5. 接入实时窗口截图。
6. 最后接入点击执行与延迟校准。
