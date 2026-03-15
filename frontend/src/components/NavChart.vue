<template>
  <div ref="chartRef" style="height: 320px"></div>
</template>

<script setup>
import * as echarts from "echarts";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { formatTime } from "../utils/time";

const props = defineProps({
  title: {
    type: String,
    default: "NAV",
  },
  points: {
    type: Array,
    default: () => [],
  },
  series: {
    type: Array,
    default: () => [],
  },
  yAxisFormatter: {
    type: String,
    default: "nav",
  },
});

const chartRef = ref(null);
let chart;

function render() {
  if (!chartRef.value) {
    return;
  }
  if (!chart) {
    chart = echarts.init(chartRef.value);
  }
  const useMultiSeries = props.series.length > 0;
  const colors = ["#163a63", "#2563eb", "#059669", "#dc2626", "#7c3aed", "#d97706"];
  const series = useMultiSeries
    ? props.series.map((item, index) => ({
        type: "line",
        name: item.name,
        smooth: false,
        showSymbol: false,
        data: item.data,
        lineStyle: { color: colors[index % colors.length], width: 2.5 },
        itemStyle: { color: colors[index % colors.length] },
      }))
    : [
        {
          type: "line",
          name: props.title,
          smooth: true,
          showSymbol: false,
          data: props.points.map((point) => point.total_nav),
          lineStyle: { color: "#2563eb", width: 3 },
          itemStyle: { color: "#2563eb" },
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(37, 99, 235, 0.24)" },
                { offset: 1, color: "rgba(37, 99, 235, 0.03)" },
              ],
            },
          },
        },
      ];

  chart.setOption({
    backgroundColor: "transparent",
    title: {
      text: props.title,
      textStyle: { color: "#0f172a", fontSize: 14, fontWeight: 700 },
    },
    xAxis: {
      type: useMultiSeries ? "time" : "category",
      data: useMultiSeries ? undefined : props.points.map((point) => new Date(point.created_at).toLocaleTimeString()),
      boundaryGap: false,
      axisLabel: {
        color: "#64748b",
        formatter: (value) => (useMultiSeries ? formatTime(value) : value),
      },
      axisLine: { lineStyle: { color: "#cbd5e1" } },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        color: "#64748b",
        formatter: (value) => (props.yAxisFormatter === "percent" ? `${Number(value).toFixed(1)}%` : value),
      },
      splitLine: { lineStyle: { color: "#e2e8f0" } },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(255,255,255,0.96)",
      borderColor: "#dbe5f0",
      textStyle: { color: "#0f172a" },
      valueFormatter: (value) => (props.yAxisFormatter === "percent" ? `${Number(value).toFixed(2)}%` : value),
    },
    legend: useMultiSeries
      ? {
          top: 8,
          right: 10,
          textStyle: { color: "#475569" },
        }
      : undefined,
    series,
    grid: { top: 40, left: 40, right: 20, bottom: 30 },
  });
}

onMounted(render);
watch(() => props.points, render, { deep: true });
watch(() => props.series, render, { deep: true });
onBeforeUnmount(() => chart?.dispose());
</script>
