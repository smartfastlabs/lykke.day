import { describe, expect, it } from "vitest";
import type { DayContextWithRoutines } from "@/types/api";

import {
  canonicalizeForSyncChecksum,
  computeSyncStateChecksum,
} from "./checksum";

describe("sync checksum", () => {
  it("canonicalizes with sorted keys and unicode preserved", () => {
    const payload = {
      z: "last",
      a: "first",
      nested: { b: 2, a: "alpha", emoji: "I ❤ Lykke" },
      list: [3, { y: "two", x: "one" }, true],
      accents: "café",
    };

    expect(canonicalizeForSyncChecksum(payload)).toBe(
      '{"a":"first","accents":"café","list":[3,{"x":"one","y":"two"},true],"nested":{"a":"alpha","b":2,"emoji":"I ❤ Lykke"},"z":"last"}',
    );
  });

  it("matches known SHA-256 cross-platform vector", () => {
    const payload = {
      z: "last",
      a: "first",
      nested: { b: 2, a: "alpha", emoji: "I ❤ Lykke" },
      list: [3, { y: "two", x: "one" }, true],
      accents: "café",
    };

    expect(
      computeSyncStateChecksum(payload as unknown as DayContextWithRoutines),
    ).toBe(
      "59668ca164948c95d7eb33c8b652979171b134dd2106fa0de0a9b1a351cfa540",
    );
  });
});
