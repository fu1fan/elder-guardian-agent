# RK3588 居家老人健康守护与环境协同 Agent

这是一个面向 RK3588 Ubuntu 22 Desktop 的 monorepo MVP。系统通过 MQTT 接入传感器、视觉事件和智能家居设备，使用 FastAPI + SQLite 持久化事件闭环，通过 WebSocket 推送到家属 dashboard 和老人本地 HMI。默认 `LLM_MOCK=true`，无需真实模型即可跑通核心验收链路。

后续使用 Agent 修 bug、加功能或重构前，请先阅读 `AGENTS.md`，它定义了本项目的分层职责、安全红线和统一开发风格。

## 架构

```text
传感器/视觉/设备模拟器
        |
        v
 Mosquitto MQTT Broker
        |
        v
 guardian-core
  ├─ Rule Engine: P0/P1/P2/P3/P4 安全分级
  ├─ Agent Runtime: 上下文、LLM/mock、解释和建议
  ├─ Action Planner: 生成高层动作
  ├─ Device Policy: 校验设备安全策略
  ├─ Action Executor: MQTT 控制、HMI、微信 mock、WebSocket
  └─ SQLite: 事件、决策、告警、HMI、设备动作复盘
        |
        ├─ elder-hmi: RK3588 本地屏幕确认
        ├─ web-dashboard: 家属/开发实时看板
        └─ wechat-adapter: mock 家属协同接口
```

## 目录

```text
configs/                  风险规则、设备策略、topic、老人画像示例
data/                     SQLite、日志、视觉快照目录
scripts/                  传感器、视觉、设备模拟和开发启动脚本
packages/guardian-shared  Python 共享枚举、schema、MQTT topic
packages/frontend-shared  前端共享类型与 API 地址工具
apps/guardian-core        FastAPI 主后端
apps/vision-service       mock 视觉服务
apps/voice-hmi-service    mock ASR/TTS HMI 服务
apps/wechat-adapter       mock 微信适配器
apps/web-dashboard        Vue 家属 dashboard
apps/elder-hmi            Vue 老人本地全屏 HMI
deploy/systemd            RK3588 systemd 示例
```

## 本地启动

```bash
conda env create -f environment.yml
conda activate elder-guardian-agent

docker compose up mosquitto

cd apps/guardian-core
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```bash
curl http://localhost:8000/health
```

前端：

```bash
pnpm install
pnpm --filter web-dashboard dev
pnpm --filter elder-hmi dev
```

打开：

- Dashboard: `http://localhost:5173`
- Elder HMI: `http://localhost:5174`
- API: `http://localhost:8000`

## MQTT Topic

```text
elder/{elder_id}/sensor/vital
elder/{elder_id}/sensor/env
elder/{elder_id}/vision/event
elder/{elder_id}/hmi/prompt
elder/{elder_id}/hmi/response
elder/{elder_id}/hmi/status
elder/{elder_id}/alert/event
elder/{elder_id}/agent/decision
elder/{elder_id}/system/status
home/{room}/{device}/set
home/{room}/{device}/state
home/{room}/{device}/ack
```

## 风险等级

- `P0`: 紧急危险，规则引擎直接告警，不等待老人确认或 LLM，例如燃气泄漏、血氧 `< 88`。
- `P1`: 高风险，本地询问并同步通知家属，例如疑似跌倒、血氧明显下降、夜间异常。
- `P2`: 中风险，先询问老人，超时后通知家属，例如长时间静止。
- `P3`: 低风险，自动控制设备或本地提醒，例如 CO2 偏高、温度异常。
- `P4`: 正常状态，仅记录和更新 dashboard。

关键约束：P0 不允许被 LLM 降级；P1 不允许被降到 P3/P4；燃气泄漏禁止风扇和空调，只允许开窗、关燃气阀、本地报警、通知家属。

## Agent 流程

```text
MQTT/API 事件
  -> 保存原始样本
  -> 规则引擎分级
  -> ContextBuilder 组装老人画像、最近数据、设备状态、历史事件
  -> LLMClient 或 mock AgentDecision
  -> OutputParser 校验 JSON
  -> Guardrails 强制安全底线
  -> ActionPlanner 生成 ask_elder / auto_control / notify_family / emergency_alert
  -> DevicePolicy 校验设备动作
  -> ActionExecutor 执行 MQTT/HMI/WebSocket/微信 mock/DB 记录
```

## 模拟验收

建议先启动设备模拟器，让设备 ack/state 能回到后端：

```bash
python scripts/simulate_device.py
```

CO2 偏高自动开窗：

```bash
python scripts/simulate_sensor.py --event co2_high
```

预期：生成 `P3` 风险事件，发布 `home/living_room/window/set` 开窗命令，dashboard 收到事件，SQLite 写入风险事件和设备动作。

长时间静止后询问老人：

```bash
python scripts/simulate_vision.py --event long_static
```

预期：生成 `P2` 风险事件，elder-hmi 收到本地询问。点击“我没事”后事件 `resolved`；点击“需要帮助”或“联系家属”后 mock 微信通知家属；超过 `HMI_RESPONSE_TIMEOUT_SEC` 无响应后升级为 `P1` 并通知家属。

燃气泄漏直接 P0 告警：

```bash
python scripts/simulate_sensor.py --event gas_leak
```

预期：直接生成 `P0`，不等待 LLM 或老人确认；发布开窗、关闭燃气阀、本地报警；不会发布风扇或空调控制。

## LLM 切换

默认 `.env.example` 中：

```bash
LLM_MOCK=true
```

此模式不会请求真实模型。要使用 OpenAI-compatible API，创建 `.env` 并设置：

```bash
LLM_MOCK=false
LLM_BASE_URL=https://your-openai-compatible-endpoint/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model
```

LLM 只输出建议动作 JSON，不允许直接发 MQTT 控制指令。所有设备控制必须经过 Action Planner 和 Device Policy。

## RK3588 部署建议

- `mosquitto` 和 `guardian-core` 可以用 Docker Compose 跑在 RK3588 上。
- `vision-service`、`voice-hmi-service` 建议用 systemd，便于后续接真实摄像头、麦克风、扬声器。
- `elder-hmi` 可用 Chromium kiosk 全屏打开 `http://127.0.0.1:5174`。
- systemd 示例在 `deploy/systemd/`，部署时把仓库放到 `/opt/elder-guardian-agent` 或按实际路径修改 `WorkingDirectory` 与 conda 路径。

## 后续扩展

- 接入真实摄像头和跌倒/姿态模型。
- 接入真实 ASR/TTS，替换 `voice-hmi-service/app/asr.py` 与 `tts.py`。
- 接入微信公众号或企业微信，替换 `wechat-adapter` mock。
- 在 RK3588 上接入 RKLLM 或本地 OpenAI-compatible 模型服务。
- 增加设备 ack 超时重试、事件复盘报表、家属多端权限。
