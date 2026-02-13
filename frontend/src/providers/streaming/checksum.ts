import { DayContextWithRoutines } from "@/types/api";

const textEncoder = new globalThis.TextEncoder();
const K = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
  0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
  0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
  0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
  0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
  0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
  0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
  0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
  0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
] as const;

const canonicalizeJsonValue = (value: unknown): string => {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new Error("Non-finite numbers are not valid JSON");
    }
    return JSON.stringify(value);
  }
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) {
    return `[${value.map((entry) => canonicalizeJsonValue(entry)).join(",")}]`;
  }
  if (value !== null && typeof value === "object") {
    const record = value as Record<string, unknown>;
    const keys = Object.keys(record).sort((left, right) =>
      left < right ? -1 : left > right ? 1 : 0,
    );
    return `{${keys
      .map((key) => `${JSON.stringify(key)}:${canonicalizeJsonValue(record[key])}`)
      .join(",")}}`;
  }
  throw new Error(`Unsupported JSON value type for checksum: ${typeof value}`);
};

const normalizeForSyncChecksum = (value: unknown): unknown => {
  if (value === null || value === undefined) return undefined;
  if (Array.isArray(value)) {
    return value.map((entry) => {
      const normalized = normalizeForSyncChecksum(entry);
      return normalized === undefined ? null : normalized;
    });
  }
  if (typeof value === "object") {
    const normalized: Record<string, unknown> = {};
    Object.entries(value as Record<string, unknown>).forEach(([key, entry]) => {
      const nextValue = normalizeForSyncChecksum(entry);
      if (nextValue !== undefined) normalized[key] = nextValue;
    });
    return normalized;
  }
  return value;
};

const rightRotate = (value: number, amount: number): number =>
  (value >>> amount) | (value << (32 - amount));

const sha256Hex = (payload: string): string => {
  const bytes = textEncoder.encode(payload);
  const bitLength = bytes.length * 8;
  const withOneByte = bytes.length + 1;
  const paddedLength = Math.ceil((withOneByte + 8) / 64) * 64;
  const padded = new Uint8Array(paddedLength);
  padded.set(bytes);
  padded[bytes.length] = 0x80;

  const lengthView = new DataView(padded.buffer);
  const high = Math.floor(bitLength / 0x100000000);
  const low = bitLength >>> 0;
  lengthView.setUint32(paddedLength - 8, high, false);
  lengthView.setUint32(paddedLength - 4, low, false);

  let h0 = 0x6a09e667;
  let h1 = 0xbb67ae85;
  let h2 = 0x3c6ef372;
  let h3 = 0xa54ff53a;
  let h4 = 0x510e527f;
  let h5 = 0x9b05688c;
  let h6 = 0x1f83d9ab;
  let h7 = 0x5be0cd19;
  const w = new Uint32Array(64);

  for (let i = 0; i < paddedLength; i += 64) {
    for (let t = 0; t < 16; t += 1) {
      w[t] = lengthView.getUint32(i + t * 4, false);
    }
    for (let t = 16; t < 64; t += 1) {
      const s0 =
        rightRotate(w[t - 15], 7) ^
        rightRotate(w[t - 15], 18) ^
        (w[t - 15] >>> 3);
      const s1 =
        rightRotate(w[t - 2], 17) ^
        rightRotate(w[t - 2], 19) ^
        (w[t - 2] >>> 10);
      w[t] = (w[t - 16] + s0 + w[t - 7] + s1) >>> 0;
    }

    let a = h0;
    let b = h1;
    let c = h2;
    let d = h3;
    let e = h4;
    let f = h5;
    let g = h6;
    let h = h7;

    for (let t = 0; t < 64; t += 1) {
      const s1 = rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25);
      const ch = (e & f) ^ (~e & g);
      const temp1 = (h + s1 + ch + K[t] + w[t]) >>> 0;
      const s0 = rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22);
      const maj = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (s0 + maj) >>> 0;

      h = g;
      g = f;
      f = e;
      e = (d + temp1) >>> 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) >>> 0;
    }

    h0 = (h0 + a) >>> 0;
    h1 = (h1 + b) >>> 0;
    h2 = (h2 + c) >>> 0;
    h3 = (h3 + d) >>> 0;
    h4 = (h4 + e) >>> 0;
    h5 = (h5 + f) >>> 0;
    h6 = (h6 + g) >>> 0;
    h7 = (h7 + h) >>> 0;
  }

  return [h0, h1, h2, h3, h4, h5, h6, h7]
    .map((value) => value.toString(16).padStart(8, "0"))
    .join("");
};

export const canonicalizeForSyncChecksum = (value: unknown): string =>
  canonicalizeJsonValue(normalizeForSyncChecksum(value));

export const computeSyncStateChecksum = (
  dayContext: DayContextWithRoutines | undefined,
): string | null => {
  if (!dayContext) return null;
  return sha256Hex(canonicalizeForSyncChecksum(dayContext));
};
