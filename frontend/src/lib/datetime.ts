export const ASTANA_GMT_OFFSET = "+05:00";
export const ASTANA_TIMEZONE_LABEL = "Астана GMT+5";

const ASTANA_OFFSET_MS = 5 * 60 * 60 * 1000;
const TZ_SUFFIX_RE = /(z|[+-]\d{2}:?\d{2})$/i;

function parseDateLike(value: string | number | Date): Date | null {
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value;
  }
  if (typeof value === "number") {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  const trimmed = value.trim();
  if (!trimmed) return null;

  const normalized = TZ_SUFFIX_RE.test(trimmed)
    ? trimmed
    : trimmed.includes("T")
      ? `${trimmed}Z`
      : `${trimmed}T00:00:00Z`;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

function astanaShiftedDate(value: string | number | Date): Date | null {
  const date = parseDateLike(value);
  if (!date) return null;
  return new Date(date.getTime() + ASTANA_OFFSET_MS);
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatAstanaDate(value?: string | number | Date | null): string {
  if (value === null || value === undefined || value === "") return "—";
  const date = astanaShiftedDate(value);
  if (!date) return "—";
  return `${pad(date.getUTCDate())}.${pad(date.getUTCMonth() + 1)}.${date.getUTCFullYear()}`;
}

export function formatAstanaShortDate(value?: string | number | Date | null): string {
  if (value === null || value === undefined || value === "") return "—";
  const date = astanaShiftedDate(value);
  if (!date) return "—";
  return `${pad(date.getUTCDate())}.${pad(date.getUTCMonth() + 1)}`;
}

export function formatAstanaDateTime(
  value?: string | number | Date | null,
  options: { seconds?: boolean; monthShort?: boolean; long?: boolean } = {}
): string {
  if (value === null || value === undefined || value === "") return "—";
  const date = astanaShiftedDate(value);
  if (!date) return "—";

  if (options.long) {
    return new Intl.DateTimeFormat("ru-RU", {
      timeZone: "UTC",
      dateStyle: "long",
      timeStyle: options.seconds ? "medium" : "short",
    }).format(date);
  }

  if (options.monthShort) {
    return new Intl.DateTimeFormat("ru-RU", {
      timeZone: "UTC",
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }

  const time = `${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}`;
  const withSeconds = options.seconds ? `${time}:${pad(date.getUTCSeconds())}` : time;
  return `${formatAstanaDate(value)} ${withSeconds}`;
}

export function astanaDateInput(value: string | number | Date = new Date()): string {
  const date = astanaShiftedDate(value);
  if (!date) return "";
  return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}`;
}

export function astanaDateInputDaysAgo(daysAgo: number): string {
  return astanaDateInput(Date.now() - daysAgo * 24 * 60 * 60 * 1000);
}

export function astanaStartOfDayParam(value?: string): string | undefined {
  if (!value) return undefined;
  return value.includes("T") ? value : `${value}T00:00:00${ASTANA_GMT_OFFSET}`;
}

export function astanaEndOfDayParam(value?: string): string | undefined {
  if (!value) return undefined;
  return value.includes("T") ? value : `${value}T23:59:59${ASTANA_GMT_OFFSET}`;
}
