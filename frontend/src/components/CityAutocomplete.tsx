"use client";

import { CITIES_FOCUS_DEFAULT, POPULAR_CITIES } from "@/lib/cities";
import { cn } from "@/lib/utils";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";

type Props = {
  value: string;
  onChange: (v: string) => void;
  id?: string;
  className?: string;
  error?: boolean;
};

function filterCities(query: string, max: number): string[] {
  const q = query.trim().toLowerCase();
  if (q.length < 2) return [];
  const out: string[] = [];
  for (const c of POPULAR_CITIES) {
    if (c.toLowerCase().includes(q)) {
      out.push(c);
      if (out.length >= max) break;
    }
  }
  return out;
}

export function CityAutocomplete({
  value,
  onChange,
  id: idProp,
  className,
  error,
}: Props) {
  const tc = useTranslations("city");
  const genId = useId();
  const inputId = idProp ?? genId;
  const listId = `${inputId}-list`;
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const wrapRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const suggestions = useMemo(() => {
    const q = value.trim();
    if (q.length >= 2) return filterCities(q, 6);
    if (open && q.length === 0) return [...CITIES_FOCUS_DEFAULT];
    return [];
  }, [value, open]);

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  useEffect(() => {
    setHighlight(0);
  }, [suggestions.length, value]);

  const pick = useCallback(
    (city: string) => {
      onChange(city);
      setOpen(false);
      inputRef.current?.blur();
    },
    [onChange]
  );

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (!open || suggestions.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => (h + 1) % suggestions.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => (h - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      const c = suggestions[highlight];
      if (c) pick(c);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div ref={wrapRef} className="relative">
      <div
        className={cn(
          "flex h-10 w-full items-center rounded-md border border-slate-300 bg-white pr-3 focus-within:ring-2 focus-within:ring-slate-400",
          error && "border-red-500 focus-within:ring-red-400",
          className
        )}
      >
        <span className="pl-3 text-slate-500 select-none" aria-hidden>
          📍
        </span>
        <input
          ref={inputRef}
          id={inputId}
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          className="min-w-0 flex-1 border-0 bg-transparent px-2 py-2 text-sm outline-none"
          placeholder={tc("placeholder")}
          autoComplete="off"
        />
      </div>
      <p className="mt-1 text-xs text-slate-500">{tc("hint")}</p>
      {open && suggestions.length > 0 && (
        <ul
          id={listId}
          role="listbox"
          className="absolute z-50 mt-1 max-h-56 w-full overflow-auto rounded-md border border-slate-200 bg-white py-1 text-sm shadow-lg"
        >
          {suggestions.map((city, i) => (
            <li
              key={city}
              role="option"
              aria-selected={i === highlight}
              className={cn(
                "cursor-pointer px-3 py-2",
                i === highlight ? "bg-slate-100" : "hover:bg-slate-50"
              )}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => pick(city)}
            >
              {city}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
