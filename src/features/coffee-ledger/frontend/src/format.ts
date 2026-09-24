export function formatDateTime(iso: string): string {
  return formatInJst(new Date(iso), false);
}

export function formatNowJst(): string {
  return formatInJst(new Date(), true);
}

function formatInJst(date: Date, withSeconds: boolean): string {
  const parts = new Intl.DateTimeFormat("ja-JP", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: withSeconds ? "2-digit" : undefined,
    hourCycle: "h23",
  }).formatToParts(date);
  const pick = (type: Intl.DateTimeFormatPartTypes): string =>
    parts.find((part) => part.type === type)?.value ?? "";
  const datePart = `${pick("year")}-${pick("month")}-${pick("day")}`;
  const timePart = withSeconds
    ? `${pick("hour")}:${pick("minute")}:${pick("second")}`
    : `${pick("hour")}:${pick("minute")}`;
  return `${datePart} ${timePart}`;
}

export function formatYen(amount: number): string {
  return `${amount.toLocaleString("ja-JP")}円`;
}

export function todayJst(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tokyo" }).format(new Date());
}

export function stepPayAmount(current: number, unpaid: number, delta: -1 | 1): number {
  if (unpaid < 1) {
    return 0;
  }
  if (unpaid < 10) {
    return unpaid;
  }
  if (delta < 0) {
    if (current % 10 !== 0) {
      return Math.max(10, Math.floor(current / 10) * 10);
    }
    return Math.max(10, current - 10);
  }
  return Math.min(unpaid, current + 10);
}
