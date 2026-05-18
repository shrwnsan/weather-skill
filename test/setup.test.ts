/**
 * Smoke test for the test/setup.ts infrastructure.
 * Validates that mockFetch and freezeTime work correctly.
 */

import { describe, expect, test, beforeEach, afterEach } from "bun:test";
import { freezeTime, restoreTime, mockFetch, restoreFetch } from "./setup";

describe("test infrastructure", () => {
  describe("mockFetch", () => {
    test("replays HKO fixture", async () => {
      const res = await fetch("https://www.hko.gov.hk/wxinfo/json/one_json.xml");
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(data).toHaveProperty("RHRREAD");
    });

    test("returns 404 for unknown URL", async () => {
      const res = await fetch("https://example.com/unknown");
      expect(res.status).toBe(404);
    });

    test("replays JMA fixtures", async () => {
      const forecast = await fetch("https://www.jma.go.jp/bosai/forecast/data/forecast/130000.json");
      expect(forecast.status).toBe(200);
      const overview = await fetch("https://www.jma.go.jp/bosai/forecast/data/overview_forecast/130000.json");
      expect(overview.status).toBe(200);
    });

    test("replays SG NEA fixtures", async () => {
      const temp = await fetch("https://api-open.data.gov.sg/v2/real-time/api/air-temperature");
      expect(temp.status).toBe(200);
    });

    test("replays US NWS fixtures", async () => {
      const points = await fetch("https://api.weather.gov/points/40.7128,-74.006");
      expect(points.status).toBe(200);
      const data = await points.json();
      expect(data).toHaveProperty("properties");
    });
  });

  describe("freezeTime", () => {
    beforeEach(freezeTime);
    afterEach(restoreTime);

    test("freezes Date.now()", () => {
      expect(Date.now()).toBe(new Date("2026-01-01T00:00:00.000Z").getTime());
    });

    test("freezes new Date()", () => {
      const d = new Date();
      expect(d.toISOString()).toBe("2026-01-01T00:00:00.000Z");
    });

    test("new Date(string) still works normally", () => {
      const d = new Date("2025-06-15T12:00:00.000Z");
      expect(d.toISOString()).toBe("2025-06-15T12:00:00.000Z");
    });
  });
});
