<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { API_BASE, type DashboardMessage, type HmiPrompt, wsUrl } from "@elder-guardian/frontend-shared";

const prompt = ref<HmiPrompt | null>(null);
const systemText = ref("系统正常守护中");
const connected = ref(false);
const sending = ref(false);

const statusText = computed(() => {
  if (!prompt.value) return "正常";
  if (prompt.value.risk_level === "P0" || prompt.value.risk_level === "P1") return "告警";
  return "注意";
});

const statusClass = computed(() => {
  if (statusText.value === "告警") return "danger";
  if (statusText.value === "注意") return "warning";
  return "normal";
});

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
    if (message.type === "hmi_prompt") {
      prompt.value = message.data as unknown as HmiPrompt;
      systemText.value = prompt.value.message;
    }
    if (message.type === "event_state" && prompt.value && message.data.event_id === prompt.value.event_id) {
      if (message.data.state === "resolved" || message.data.state === "recorded") {
        prompt.value = null;
        systemText.value = "已确认，系统继续守护中";
      }
    }
    if (message.type === "hmi_timeout" && prompt.value && message.data.prompt_id === prompt.value.prompt_id) {
      systemText.value = "未收到回复，已通知家属";
    }
  };
}

async function respond(responseType: "safe" | "help" | "contact_family", responseText: string) {
  if (!prompt.value || sending.value) return;
  sending.value = true;
  await fetch(`${API_BASE}/api/hmi/response`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt_id: prompt.value.prompt_id,
      event_id: prompt.value.event_id,
      elder_id: prompt.value.elder_id,
      response_type: responseType,
      response_text: responseText
    })
  });
  systemText.value = responseText === "我没事" ? "收到，已记录您安全" : "收到，正在联系家属";
  sending.value = false;
}

onMounted(connectWs);
</script>

<template>
  <main class="screen" :class="statusClass">
    <section class="topbar">
      <span>居家健康守护</span>
      <span>{{ connected ? "已连接" : "连接中" }}</span>
    </section>

    <section class="status">
      <p>当前状态</p>
      <h1>{{ statusText }}</h1>
      <h2>{{ systemText }}</h2>
    </section>

    <section class="actions">
      <button class="safe" :disabled="!prompt || sending" @click="respond('safe', '我没事')">我没事</button>
      <button class="help" :disabled="!prompt || sending" @click="respond('help', '需要帮助')">需要帮助</button>
      <button class="family" :disabled="!prompt || sending" @click="respond('contact_family', '联系家属')">联系家属</button>
    </section>
  </main>
</template>

