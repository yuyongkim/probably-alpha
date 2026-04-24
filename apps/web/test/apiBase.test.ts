// Tests for lib/apiBase.ts — the runtime API-host resolver.
// We reset the module registry each case so process.env / window.location
// reads in `apiBase` are observed fresh.
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

const ENV_KEY = "NEXT_PUBLIC_API_BASE_URL";

async function freshApiBase() {
  vi.resetModules();
  const mod = await import("@/lib/apiBase");
  return mod.apiBase;
}

function setLocation(href: string) {
  // jsdom's Location is read-only; replace via Object.defineProperty.
  const url = new URL(href);
  Object.defineProperty(window, "location", {
    configurable: true,
    value: {
      ...window.location,
      href: url.href,
      protocol: url.protocol,
      hostname: url.hostname,
      host: url.host,
      port: url.port,
      origin: url.origin,
      pathname: url.pathname,
    },
  });
}

describe("apiBase", () => {
  const originalEnv = process.env[ENV_KEY];

  beforeEach(() => {
    delete process.env[ENV_KEY];
  });

  afterEach(() => {
    if (originalEnv === undefined) delete process.env[ENV_KEY];
    else process.env[ENV_KEY] = originalEnv;
  });

  it("SSR (no window) uses env var when set", async () => {
    const savedWindow = globalThis.window;
    // @ts-expect-error — deliberately undefining for SSR path.
    delete globalThis.window;
    process.env[ENV_KEY] = "https://api.example.test";
    const apiBase = await freshApiBase();
    expect(apiBase()).toBe("https://api.example.test");
    globalThis.window = savedWindow;
  });

  it("SSR (no window) falls back to loopback when env unset", async () => {
    const savedWindow = globalThis.window;
    // @ts-expect-error — deliberately undefining for SSR path.
    delete globalThis.window;
    const apiBase = await freshApiBase();
    expect(apiBase()).toBe("http://127.0.0.1:31300");
    globalThis.window = savedWindow;
  });

  it("localhost uses :31300 fallback when env unset", async () => {
    setLocation("http://localhost:3000/");
    const apiBase = await freshApiBase();
    expect(apiBase()).toBe("http://localhost:31300");
  });

  it("127.0.0.1 uses :31300 fallback when env unset", async () => {
    setLocation("http://127.0.0.1:3000/");
    const apiBase = await freshApiBase();
    expect(apiBase()).toBe("http://127.0.0.1:31300");
  });

  it("localhost prefers env var when set", async () => {
    setLocation("http://localhost:3000/");
    process.env[ENV_KEY] = "http://my.dev.api";
    const apiBase = await freshApiBase();
    expect(apiBase()).toBe("http://my.dev.api");
  });

  it("gazua.yule.pics → gazua-api.yule.pics", async () => {
    setLocation("https://gazua.yule.pics/dashboard");
    const apiBase = await freshApiBase();
    expect(apiBase()).toBe("https://gazua-api.yule.pics");
  });

  it("alpha.yule.pics → alpha-api.yule.pics", async () => {
    setLocation("https://alpha.yule.pics/");
    const apiBase = await freshApiBase();
    expect(apiBase()).toBe("https://alpha-api.yule.pics");
  });

  it("hostname with no dot falls back to same-origin", async () => {
    setLocation("https://intranet/");
    const apiBase = await freshApiBase();
    expect(apiBase()).toBe("https://intranet");
  });

  it("hostname with no dot prefers env var when set", async () => {
    setLocation("https://intranet/");
    process.env[ENV_KEY] = "https://alt.api";
    const apiBase = await freshApiBase();
    expect(apiBase()).toBe("https://alt.api");
  });
});
