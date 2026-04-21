import { useEffect, useRef } from "react";
import { createChart, type IChartApi, type ISeriesApi, LineStyle } from "lightweight-charts";
import type { Candle } from "../types";

type Props = { candles: Candle[] };

export function PriceMini({ candles }: Props) {
  const ref = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = createChart(ref.current, {
      layout: { background: { color: "transparent" }, textColor: "#8A93A0" },
      grid: { vertLines: { visible: false }, horzLines: { color: "#222831", style: LineStyle.Dotted } },
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false, timeVisible: true, secondsVisible: false },
      width: ref.current.clientWidth,
      height: 120,
    });
    const series = chart.addAreaSeries({
      lineColor: "#6D8CFF",
      topColor: "rgba(109,140,255,0.35)",
      bottomColor: "rgba(109,140,255,0.0)",
      lineWidth: 2,
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const onResize = () => {
      if (ref.current && chartRef.current) chartRef.current.applyOptions({ width: ref.current.clientWidth });
    };
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current) return;
    const data = candles.map((c) => ({
      time: Math.floor(new Date(c.ts).getTime() / 1000) as any,
      value: c.c,
    }));
    seriesRef.current.setData(data);
  }, [candles]);

  return <div ref={ref} className="w-full" />;
}
