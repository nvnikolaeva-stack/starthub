import { test, expect } from "@playwright/test";

test.describe("Переключение языка", () => {
  test("кнопка языка видна", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");

    const en = page.getByRole("button", { name: /english/i });
    const ru = page.getByRole("button", { name: /русский/i });
    await expect(en.or(ru).first()).toBeVisible();
  });

  test("переключение на английский", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");
    await page.waitForTimeout(400);

    const toEn = page.getByRole("button", { name: "English" });
    if ((await toEn.count()) === 0) {
      await expect(
        page.getByRole("heading", { name: /event calendar/i })
      ).toBeVisible();
      return;
    }
    await toEn.click();
    await expect(page.getByRole("heading", { name: "Event calendar" })).toBeVisible({
      timeout: 20_000,
    });
  });

  test("переключение обратно на русский", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");
    await page.waitForTimeout(400);

    const toEn = page.getByRole("button", { name: "English" });
    if ((await toEn.count()) > 0) {
      await toEn.click();
      await expect(page.getByRole("heading", { name: "Event calendar" })).toBeVisible({
        timeout: 20_000,
      });
    }

    const toRu = page.getByRole("button", { name: "Русский" });
    await expect(toRu).toBeVisible();
    await toRu.click();
    await expect(
      page.getByRole("heading", { name: "Календарь стартов" })
    ).toBeVisible({ timeout: 20_000 });
  });
});
