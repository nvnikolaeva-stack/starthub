import { defineRouting } from "next-intl/routing";

import { LOCALE_STORAGE_KEY } from "@/i18n/localeCookie";

export const routing = defineRouting({
  locales: ["ru"],
  defaultLocale: "ru",
  localePrefix: "never",
  localeCookie: {
    name: LOCALE_STORAGE_KEY,
    maxAge: 60 * 60 * 24 * 365,
    sameSite: "lax",
    path: "/",
  },
});

export type AppLocale = (typeof routing.locales)[number];
