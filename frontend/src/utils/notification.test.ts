import { describe, expect, it } from "vitest";
import {
  formatNotificationDateTime,
  getEntityTypeLabel,
  parseContent,
  safeStringify,
} from "@/utils/notification";

describe("notification utils", () => {
  it("safeStringify returns string input unchanged", () => {
    expect(safeStringify("hello")).toBe("hello");
  });

  it("safeStringify stringifies objects", () => {
    expect(safeStringify({ a: 1 })).toContain('"a": 1');
  });

  it("parseContent returns parsed object when content is JSON object", () => {
    expect(parseContent('{"body":"Hi"}')).toEqual({ body: "Hi" });
  });

  it("parseContent returns null for invalid JSON", () => {
    expect(parseContent("not-json")).toBeNull();
  });

  it("formatNotificationDateTime returns original value for invalid date", () => {
    expect(formatNotificationDateTime("not-a-date")).toBe("not-a-date");
  });

  it("getEntityTypeLabel maps known values and falls back for unknown", () => {
    expect(getEntityTypeLabel("task")).toBe("Task");
    expect(getEntityTypeLabel("calendar_entry")).toBe("Event");
    expect(getEntityTypeLabel("custom_type")).toBe("custom type");
  });
});
