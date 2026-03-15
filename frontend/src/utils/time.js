const APP_TIME_ZONE = import.meta.env.APP_TIMEZONE || "Asia/Shanghai";

function normalize(value) {
  if (!value) {
    return null;
  }
  if (value instanceof Date) {
    return value;
  }
  if (typeof value === "number") {
    return new Date(value);
  }
  if (typeof value === "string") {
    const hasZone = /[zZ]|[+-]\d{2}:\d{2}$/.test(value);
    return new Date(hasZone ? value : `${value}Z`);
  }
  return null;
}

export function toTimestamp(value) {
  const date = normalize(value);
  return date ? date.getTime() : null;
}

export function formatDateTime(value) {
  const date = normalize(value);
  if (!date || Number.isNaN(date.getTime())) {
    return "-";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: APP_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

export function formatTime(value) {
  const date = normalize(value);
  if (!date || Number.isNaN(date.getTime())) {
    return "-";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: APP_TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}
