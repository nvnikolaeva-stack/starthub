"use client";

import { LOCALE_STORAGE_KEY } from "@/i18n/localeCookie";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** Синхронизация localStorage → cookie при первом заходе (язык из прошлой сессии). */
export function LocaleSync() {
  const router = useRouter();
  useEffect(() => {
    try {
      const saved = localStorage.getItem(LOCALE_STORAGE_KEY);
      if (saved !== "en" && saved !== "ru") return;
      const m = document.cookie.match(
        new RegExp(`(?:^|; )${LOCALE_STORAGE_KEY}=([^;]*)`)
      );
      const cur = m?.[1];
      if (cur !== saved) {
        document.cookie = `${LOCALE_STORAGE_KEY}=${saved};path=/;max-age=31536000;SameSite=Lax`;
        router.refresh();
      }
    } catch {
      /* ignore */
    }
  }, [router]);
  return null;
}
