/**
 * Unit tests: token refresh logic.
 * Правило jwt.md: lifecycle, revocation, expiration.
 */
import { describe, it, expect } from "vitest";

const REFRESH_BEFORE_MS = 5 * 60 * 1000;

function shouldRefresh(expiresAtMs: number): boolean {
  return expiresAtMs - Date.now() < REFRESH_BEFORE_MS;
}

describe("Token refresh logic", () => {
  it("should not refresh when token has plenty of time", () => {
    const future = Date.now() + 60 * 60 * 1000; // 1 hour
    expect(shouldRefresh(future)).toBe(false);
  });

  it("should refresh when token expires in < 5 min", () => {
    const soon = Date.now() + 4 * 60 * 1000; // 4 minutes
    expect(shouldRefresh(soon)).toBe(true);
  });

  it("should refresh expired token", () => {
    const past = Date.now() - 1000;
    expect(shouldRefresh(past)).toBe(true);
  });

  it("should refresh at exactly 5 minutes boundary", () => {
    const boundary = Date.now() + REFRESH_BEFORE_MS - 100;
    expect(shouldRefresh(boundary)).toBe(true);
  });
});
