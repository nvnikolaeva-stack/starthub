import { test, expect } from "@playwright/test";

async function noHorizontalOverflow(page: import("@playwright/test").Page) {
  const { scrollWidth, clientWidth } = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 8);
}

test.describe("Мобильная версия", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
  });

  test("нет горизонтального скролла на главной", async ({ page }) => {
    await page.goto("/");
    await page.waitForTimeout(800);
    await noHorizontalOverflow(page);
  });

  test("нет горизонтального скролла на /add", async ({ page }) => {
    await page.goto("/add");
    await page.waitForTimeout(800);
    await noHorizontalOverflow(page);
  });

  test("нет горизонтального скролла на /stats", async ({ page }) => {
    await page.goto("/stats");
    await page.waitForTimeout(800);
    await noHorizontalOverflow(page);
  });

  test("бургер-меню или пункты навигации доступны", async ({ page }) => {
    await page.goto("/");
    await page.waitForTimeout(500);

    const burger = page.getByRole("button", { name: /меню|menu/i });
    await expect(burger).toBeVisible();
  });

  test("форма /add юзабельна на мобильном", async ({ page }) => {
    await page.goto("/add");
    await page.waitForTimeout(500);
    const firstField = page.locator("select, input, textarea").first();
    await expect(firstField).toBeVisible();
  });

  test("карточки событий не шире экрана", async ({ page }) => {
    await page.goto("/");
    await page.waitForTimeout(1000);

    const links = page.locator('a[href^="/event/"]');
    const count = await links.count();
    const check = Math.min(count, 3);
    for (let i = 0; i < check; i++) {
      const box = await links.nth(i).boundingBox();
      if (box) {
        expect(box.width).toBeLessThanOrEqual(375 + 8);
      }
    }
  });
});
