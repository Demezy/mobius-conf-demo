export type EventRow = {
  id: number;
  session_id: string;
  machine_id: string;
  event_type: string;
  tool_name: string | null;
  created_at: string;
  payload?: any;
};

export async function fetchEvents(machineId?: string): Promise<EventRow[]> {
  const qs = machineId ? `?machine_id=${encodeURIComponent(machineId)}` : "";
  const r = await fetch(`/events${qs}`);
  if (!r.ok) throw new Error("fetch failed");
  return r.json();
}

export function openWs(onMsg: (data: any) => void): WebSocket {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onmessage = (ev) => {
    try {
      onMsg(JSON.parse(ev.data));
    } catch {
      // swallow
    }
  };
  return ws;
}
