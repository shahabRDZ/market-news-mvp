import { useEffect, useRef } from "react";
import { WS_URL } from "./client";
import type { WsFrame } from "../types";

export function useRealtime(onFrame: (f: WsFrame) => void) {
  const retries = useRef(0);
  useEffect(() => {
    let cancelled = false;
    let ws: WebSocket | null = null;
    let retryTimer: number | undefined;

    const connect = () => {
      if (cancelled) return;
      try {
        ws = new WebSocket(WS_URL);
      } catch {
        scheduleRetry();
        return;
      }
      ws.onopen = () => {
        retries.current = 0;
      };
      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data) as WsFrame;
          onFrame(data);
        } catch {
          // ignore malformed frame
        }
      };
      ws.onclose = () => {
        scheduleRetry();
      };
      ws.onerror = () => {
        ws?.close();
      };
    };

    const scheduleRetry = () => {
      if (cancelled) return;
      retries.current = Math.min(retries.current + 1, 6);
      const delay = Math.min(30000, 500 * 2 ** retries.current);
      retryTimer = window.setTimeout(connect, delay);
    };

    connect();
    return () => {
      cancelled = true;
      if (retryTimer) window.clearTimeout(retryTimer);
      ws?.close();
    };
  }, [onFrame]);
}
