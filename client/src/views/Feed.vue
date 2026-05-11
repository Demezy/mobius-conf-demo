<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from "vue";
import { fetchEvents, openWs, type EventRow } from "../api";

const events = ref<EventRow[]>([]);
const machineFilter = ref<string>("");
let ws: WebSocket | null = null;

const visible = computed(() => {
  if (!machineFilter.value) return events.value;
  return events.value.filter((e) => e.machine_id === machineFilter.value);
});

async function load() {
  try {
    const rows = await fetchEvents();
    events.value = rows;
  } catch (e) {
    // ignore
  }
}

function prepend(data: any) {
  // websocket pushes a partial row (no payload field); fine for live feed
  const row: EventRow = {
    id: data.id,
    session_id: data.session_id,
    machine_id: data.machine_id,
    event_type: data.event_type,
    tool_name: data.tool ?? null,
    created_at: data.created_at,
  };
  // dedup
  if (events.value.find((x) => x.id === row.id)) return;
  events.value = [row, ...events.value];
}

onMounted(async () => {
  await load();
  ws = openWs(prepend);
});

onUnmounted(() => {
  if (ws) ws.close();
});
</script>

<template>
  <div>
    <div class="controls">
      <input
        v-model="machineFilter"
        placeholder="filter by machine_id"
      />
      <button @click="load">refresh</button>
    </div>
    <ul class="feed">
      <li v-for="e in visible" :key="e.id" class="row">
        <span class="type" :class="e.event_type">{{ e.event_type }}</span>
        <span class="tool">{{ e.tool_name ?? "—" }}</span>
        <span class="machine">{{ e.machine_id }}</span>
        <span class="session">{{ e.session_id.slice(0, 8) }}</span>
        <span class="ts">{{ e.created_at }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.controls {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.controls input {
  flex: 1;
  padding: 6px 10px;
  background: #1b1f27;
  border: 1px solid #2a2f3a;
  color: #d8dee9;
  border-radius: 4px;
}
.controls button {
  padding: 6px 12px;
  background: #2a2f3a;
  border: 1px solid #3a4150;
  color: #d8dee9;
  border-radius: 4px;
  cursor: pointer;
}
.feed {
  list-style: none;
  padding: 0;
  margin: 0;
}
.row {
  display: grid;
  grid-template-columns: 110px 140px 140px 80px 1fr;
  gap: 12px;
  padding: 6px 8px;
  border-bottom: 1px solid #1b1f27;
  font-family: ui-monospace, monospace;
  font-size: 12px;
}
.type {
  color: #88c0d0;
}
.type.SessionStart,
.type.SessionEnd {
  color: #a3be8c;
}
.tool {
  color: #ebcb8b;
}
.machine {
  color: #b48ead;
}
.session {
  color: #7a8597;
}
.ts {
  color: #5e6776;
}
</style>
