<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { API_BASE, type DashboardMessage, wsUrl } from "@elder-guardian/frontend-shared";

type AnyRecord = Record<string, any>;

const connected = ref(false);
const state = reactive<AnyRecord>({
  elder_status: "加载中",
  current_risk_level: "P4",
  latest_vital: null,
  latest_env: null,
  events: [],
  agent_runs: [],
  devices: [],
  alerts: []
});
const liveLog = ref<AnyRecord[]>([]);

const latestRoom = computed(() => state.latest_env?.room ?? state.recent_vision?.[0]?.room ?? "living_room");

async function loadState() {
  const response = await fetch(`${API_BASE}/api/dashboard/state`);
  Object.assign(state, await response.json());
}

function upsertDevice(deviceState: AnyRecord) {
  const index = state.devices.findIndex((item: AnyRecord) => item.room === deviceState.room && item.device === deviceState.device);
  if (index >= 0) state.devices[index] = { ...state.devices[index], ...deviceState };
  else state.devices.unshift(deviceState);
}

function prepend(listName: string, item: AnyRecord, limit = 30) {
  state[listName] = [item, ...(state[listName] ?? [])].slice(0, limit);
}

function connectWs() {
  const ws = new WebSocket(wsUrl());
  ws.onopen = () => {
    connected.value = true;
  };
  ws.onclose = () => {
    connected.value = false;
    window.setTimeout(connectWs, 2000);
  };
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data) as DashboardMessage;
    liveLog.value = [message, ...liveLog.value].slice(0, 60);
    if (message.type === "dashboard_state") Object.assign(state, message.data);
    if (message.type === "sensor_vital") state.latest_vital = message.data;
    if (message.type === "sensor_env") state.latest_env = message.data;
    if (message.type === "risk_event") {
      prepend("events", message.data);
      state.current_risk_level = message.data.risk_level;
      state.elder_status = message.data.risk_level === "P4" ? "正常" : "注意";
    }
    if (message.type === "agent_decision") prepend("agent_runs", { decision: message.data, created_at: message.timestamp });
    if (message.type === "alert" || message.type === "emergency_alert") prepend("alerts", message.data);
    if (message.type === "device_state") upsertDevice(message.data);
  };
}

async function command(room: string, device: string, action: string, value: unknown = null) {
  await fetch(`${API_BASE}/api/home/device/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ room, device, action, value, reason: "Dashboard manual control" })
  });
}

onMounted(async () => {
  await loadState();
  connectWs();
});
</script>

<template>
  <main class="dashboard">
    <header>
      <div>
        <h1>居家老人健康守护 Dashboard</h1>
        <p>{{ connected ? "实时连接已建立" : "正在连接 WebSocket" }}</p>
      </div>
      <strong :class="state.current_risk_level">{{ state.current_risk_level }}</strong>
    </header>

    <section class="metrics">
      <article>
        <span>老人状态</span>
        <b>{{ state.elder_status }}</b>
      </article>
      <article>
        <span>心率</span>
        <b>{{ state.latest_vital?.heart_rate ?? "--" }}</b>
      </article>
      <article>
        <span>血氧</span>
        <b>{{ state.latest_vital?.spo2 ?? "--" }}%</b>
      </article>
      <article>
        <span>CO2</span>
        <b>{{ state.latest_env?.co2_ppm ?? "--" }}</b>
      </article>
      <article>
        <span>温度</span>
        <b>{{ state.latest_env?.temperature ?? "--" }}°C</b>
      </article>
      <article>
        <span>当前房间</span>
        <b>{{ latestRoom }}</b>
      </article>
    </section>

    <section class="grid">
      <article class="panel">
        <h2>风险事件</h2>
        <ul>
          <li v-for="event in state.events" :key="event.event_id">
            <strong>{{ event.risk_level }}</strong>
            <span>{{ event.event_type }}</span>
            <p>{{ event.summary }}</p>
          </li>
        </ul>
      </article>

      <article class="panel">
        <h2>Agent 决策</h2>
        <ul>
          <li v-for="run in state.agent_runs" :key="run.run_id ?? run.created_at">
            <strong>{{ run.decision?.risk_level ?? run.decision?.alert_priority ?? "--" }}</strong>
            <p>{{ run.decision?.reasoning_summary ?? run.decision?.summary ?? "等待决策" }}</p>
          </li>
        </ul>
      </article>

      <article class="panel">
        <h2>智能家居</h2>
        <div class="devices">
          <div v-for="device in state.devices" :key="`${device.room}/${device.device}`">
            <span>{{ device.room }}/{{ device.device }}</span>
            <b>{{ device.state }}</b>
          </div>
        </div>
        <div class="controls">
          <button @click="command('living_room', 'window', 'open')">开窗</button>
          <button @click="command('living_room', 'window', 'close')">关窗</button>
          <button @click="command('living_room', 'fan', 'turn_on')">开风扇</button>
          <button @click="command('living_room', 'fan', 'turn_off')">关风扇</button>
          <button @click="command('bedroom', 'light', 'turn_on')">开灯</button>
          <button @click="command('bedroom', 'light', 'turn_off')">关灯</button>
        </div>
      </article>

      <article class="panel">
        <h2>告警与实时消息</h2>
        <ul>
          <li v-for="alert in state.alerts" :key="alert.alert_id">
            <strong>{{ alert.priority }}</strong>
            <p>{{ alert.message }}</p>
          </li>
        </ul>
        <ol class="log">
          <li v-for="item in liveLog" :key="`${item.timestamp}-${item.type}`">{{ item.type }}</li>
        </ol>
      </article>
    </section>
  </main>
</template>

