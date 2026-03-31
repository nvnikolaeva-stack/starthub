import { defineConfig, devices } from "@playwright/test";

/**
 * База: http://localhost:3000
 *
 * Перед `npm run e2e` запустите бэкенд (:8000) и фронт:
 *   cd frontend && npm run dev
 *
 * Чтобы Playwright сам поднял `next dev` (если порт 3000 свободен и другого
 * `next dev` по этому проекту нет):
 *   PLAYWRIGHT_START_DEV=1 npm run e2e
 */
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  workers: process.env.CI ? 2 : 3,
  retries: process.env.CI ? 1 : 0,
  forbidOnly: !!process.env.CI,
  reporter: [["html", { open: "never" }], ["list"]],
  use: {
    baseURL,
    headless: process.env.PW_HEADED !== "1",
    screenshot: "only-on-failure",
    trace: "on-first-retry",
    ...devices["Desktop Chrome"],
  },
  ...(process.env.PLAYWRIGHT_START_DEV === "1"
    ? {
        webServer: {
          command: "npm run dev",
          url: baseURL,
          reuseExistingServer: true,
          timeout: 120_000,
        },
      }
    : {}),
});
