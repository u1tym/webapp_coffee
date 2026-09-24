export function isAdminRoute(path: string): boolean {
  return path === "/admin" || path.startsWith("/admin/");
}

let unlocked = false;

export function isAdminUnlocked(): boolean {
  return unlocked;
}

export function unlockAdmin(): void {
  unlocked = true;
}

export function lockAdmin(): void {
  unlocked = false;
}

export function safeAdminNext(value: unknown): string {
  if (typeof value !== "string") {
    return "/admin";
  }
  const path = value.split("?")[0] ?? value;
  if (!isAdminRoute(path) || path.startsWith("//")) {
    return "/admin";
  }
  return value;
}

export function matchesAdminPassword(value: string): boolean {
  return value === import.meta.env.VITE_COFFEE_LEDGER_ADMIN_PASSWORD;
}
