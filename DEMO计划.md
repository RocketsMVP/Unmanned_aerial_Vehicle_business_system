## Demo 实现计划

### 一、技术选型总览

**语言**：Python 3.11（后端 + AI）、TypeScript / Vue 3（前端）

**核心框架与开源库**：

| 层次 | 选型 | 说明 |
|------|------|------|
| 前端框架 | Vue 3 + Vite + Element Plus | 快速搭建多角色管理界面 |
| GIS 地图 | Leaflet.js（2D）/ CesiumJS（3D地形） | Cesium 有免费 OSM 底图，适合山地可视化 |
| 图表 | ECharts 5 | 仪表盘、实时折线、风险雷达图 |
| 后端 API | FastAPI + Uvicorn | 自带 WebSocket，异步性能好 |
| 任务队列 | Celery + Redis | 异步处理 AI 推理、报告生成 |
| AI 检测 | YOLOv8（ultralytics） | pip 直接装，支持 ONNX 部署 |
| 路径规划 | OSRM（Docker 一键起） | 支持重庆 OSM 路网，<2s 响应 |
| 空间数据库 | PostgreSQL + PostGIS | 地理围栏、路段查询 |
| 缓存/推送 | Redis | 实时遥测、WebSocket 广播 |
| 无人机仿真 | MAVLink + ArduPilot SITL | 模拟 GPS 轨迹，不需要真机 |
| 视频流 | MediaMTX + FFmpeg | 推 RTSP → HLS，前端 Video.js 播放 |
| 对象存储 | MinIO | 存图片、视频片段、报告 PDF |

---

### 二、模块拆解与实现方式

**模块 1：险情上报 + 无人机调度（应急快速响应）**

后端用 FastAPI 建 `/incidents` REST 接口，前端用 Leaflet.js 在地图上点击上报。调度逻辑用 PostGIS 的 `ST_Distance` 查出最近空闲无人机，通过 WebSocket 下发起飞指令给 SITL 仿真器。路径规划调 OSRM 的 `/route` 接口，返回 GeoJSON 直接在地图上渲染。

**模块 2：AI 态势感知**

用 YOLOv8s（小模型，够快）加载预训练权重，在 Celery worker 里跑推理。Demo 阶段用公开数据集（DOTA、BDD100K、VisDrone）的图片模拟无人机视角。识别结果（事故类型、人员框、车辆损毁）通过 WebSocket 推到前端，ECharts 实时更新置信度仪表盘。

**模块 3：多部门协同处置**

前端 GIS 大屏用 CesiumJS 渲染重庆山地地形（加载 Cesium Ion 免费地形 + OSM Buildings），各部门救援车辆用不同颜色 Marker 实时更新位置。最优路径由 OSRM 计算，支持「新增阻断 → 自动重规划」逻辑（后端 Celery 定时轮询）。视频回传用 MediaMTX 模拟一路 RTSP 流，Video.js 嵌入前端。

**模块 4：复盘报告**

处置全程事件写 PostgreSQL，结束后 Celery task 自动统计各环节耗时、资源利用率，生成 JSON → ECharts 图表，支持导出 PDF（用 WeasyPrint 或 pdfkit）。

---

### 三、推荐 Demo 最小可行版（MVP）路径

分三周可以跑起来一个能演示的 Demo：

第一周，把底座搭好：FastAPI 项目骨架 + PostgreSQL/PostGIS + Redis，Leaflet.js 前端能在地图上点击上报险情，WebSocket 推送实时消息，MAVLink SITL 仿真无人机飞行轨迹在地图上动起来。

第二周，接入 AI 和路径：YOLOv8 加载 VisDrone 预训练权重，做一个上传图片 → 返回识别框的接口，前端展示结果。OSRM Docker 起好，接入路径规划，地图上展示最优救援路径和动态重规划。

第三周，补全协同和复盘：CesiumJS 换掉 Leaflet 做 3D 地形演示，MediaMTX 模拟视频回传，复盘报告自动生成 + ECharts 展示。做一轮端到端演示流程录屏。
