"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Plus } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_LINKS: { href: string; labelKey: "calendar" | "stats" }[] = [
  { href: "/", labelKey: "calendar" },
  { href: "/stats", labelKey: "stats" },
];

function linkClass(pathname: string, href: string) {
  const active =
    href === "/"
      ? pathname === "/" || pathname === ""
      : pathname === href || pathname.startsWith(`${href}/`);
  return cn(
    "inline-flex min-h-11 items-center rounded-md px-2 py-1.5 text-sm transition-colors no-underline",
    active
      ? "font-medium text-[var(--color-primary)]"
      : "text-[var(--color-text-secondary)] hover:text-[var(--color-text)]"
  );
}

export function Navbar() {
  const pathname = usePathname() || "";
  const [open, setOpen] = useState(false);
  const t = useTranslations("nav");

  const links = (
    <>
      {NAV_LINKS.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={linkClass(pathname, item.href)}
          onClick={() => setOpen(false)}
        >
          {t(item.labelKey)}
        </Link>
      ))}
    </>
  );

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)]/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-2 px-4">
        <Link
          href="/"
          className="flex min-w-0 items-center text-lg font-semibold text-[var(--color-text)]"
        >
          <span className="truncate">{t("brand")}</span>
        </Link>

        <nav className="hidden flex-1 items-center justify-center gap-6 md:flex">
          {links}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <Link
            href="/add"
            className={cn(
              "inline-flex min-h-11 items-center justify-center rounded-[var(--radius-full)] px-4 text-sm font-semibold no-underline",
              "bg-[var(--color-accent)] text-[var(--color-accent-text)]",
              "hover:opacity-95"
            )}
          >
            {t("newEventCta")}
          </Link>
        </div>

        <div className="flex items-center gap-1 md:hidden">
          <Link
            href="/add"
            className={cn(
              "flex h-11 w-11 shrink-0 items-center justify-center rounded-[var(--radius-full)] no-underline",
              "bg-[var(--color-accent)] text-[var(--color-accent-text)]"
            )}
            aria-label={t("newEventShortAria")}
          >
            <Plus size={22} strokeWidth={2.5} />
          </Link>
          <button
            type="button"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md text-[var(--color-text)]"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-label={t("menuAria")}
          >
            {open ? "✕" : "☰"}
          </button>
        </div>
      </div>

      {open && (
        <div className="flex flex-col gap-2 border-t border-[var(--color-border)] px-4 py-3 md:hidden">
          <div className="flex flex-col gap-1 pl-1">{links}</div>
        </div>
      )}
    </header>
  );
}
