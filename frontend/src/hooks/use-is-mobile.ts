"use client";

import { useEffect, useState } from "react";

/** Aligns with calendar/layout mobile breakpoint (Tailwind `md`: 768px). */
const QUERY = "(max-width: 767px)";

export function useIsMobile(): boolean {
  const [m, setM] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia(QUERY);
    const fn = () => setM(mq.matches);
    fn();
    mq.addEventListener("change", fn);
    return () => mq.removeEventListener("change", fn);
  }, []);
  return m;
}
