/**
 * Unit tests: password strength validation.
 * Правило testing.md: тестировать validation.
 */
import { describe, it, expect } from "vitest";

// Password validation logic (mirrors backend rules)
function validatePassword(
  password: string,
  minLength = 8,
  requireUpper = false,
  requireSpecial = false,
): string[] {
  const errors: string[] = [];
  if (password.length < minLength)       errors.push(`Минимум ${minLength} символов`);
  if (!/[A-Za-z]/.test(password))        errors.push("Нужна буква");
  if (!/\d/.test(password))              errors.push("Нужна цифра");
  if (requireUpper && !/[A-Z]/.test(password)) errors.push("Нужна заглавная буква");
  if (requireSpecial && !/[!@#$%^&*]/.test(password)) errors.push("Нужен спецсимвол");
  return errors;
}

describe("Password validation", () => {
  it("accepts valid password", () => {
    expect(validatePassword("MyPass1234")).toHaveLength(0);
  });

  it("rejects too short", () => {
    const errs = validatePassword("Ab1");
    expect(errs.some(e => e.includes("символов"))).toBe(true);
  });

  it("rejects no letter", () => {
    const errs = validatePassword("12345678");
    expect(errs.some(e => e.includes("буква"))).toBe(true);
  });

  it("rejects no digit", () => {
    const errs = validatePassword("NoDigitsHere");
    expect(errs.some(e => e.includes("цифра"))).toBe(true);
  });

  it("respects requireUpper flag", () => {
    const errs = validatePassword("lowercase1", 8, true);
    expect(errs.some(e => e.includes("заглавная"))).toBe(true);
  });

  it("passes with uppercase when required", () => {
    const errs = validatePassword("Uppercase1", 8, true);
    expect(errs).toHaveLength(0);
  });

  it("respects requireSpecial flag", () => {
    const errs = validatePassword("NoSpecial1", 8, false, true);
    expect(errs.some(e => e.includes("спецсимвол"))).toBe(true);
  });

  it("passes all requirements", () => {
    const errs = validatePassword("MyP@ssword1", 8, true, true);
    expect(errs).toHaveLength(0);
  });
});
