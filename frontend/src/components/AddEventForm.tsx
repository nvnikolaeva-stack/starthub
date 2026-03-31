"use client";

import type { Event, SportType } from "@/lib/types";
import {
  ApiError,
  createEvent,
  createParticipant,
  createRegistration,
  getDistances,
} from "@/lib/api";
import { CityAutocomplete } from "@/components/CityAutocomplete";
import {
  FriendEntry,
  ParticipantSelector,
} from "@/components/ParticipantSelector";
import { dayKey, parseISODate } from "@/lib/dates";
import { EventCard } from "@/components/EventCard";
import { SportIcon } from "@/components/SportIcon";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";
import { useIsMobile } from "@/hooks/use-is-mobile";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
} from "react";

const SPORT_VALUES: SportType[] = [
  "swimming",
  "running",
  "cycling",
  "triathlon",
  "other",
];

const SPORT_MSG_KEY: Record<SportType, string> = {
  swimming: "sportSwimming",
  running: "sportRunning",
  cycling: "sportCycling",
  triathlon: "sportTriathlon",
  other: "sportOther",
};

const DAY_OPTIONS = [2, 3, 4, 5, 6, 7] as const;

function addDaysToIso(iso: string, add: number): string {
  const [y, m, d] = iso.split("-").map(Number);
  const dt = new Date(y, m - 1, d + add);
  return dayKey(dt);
}

function daysBetween(startIso: string, endIso: string): number {
  const a = parseISODate(startIso);
  const b = parseISODate(endIso);
  return Math.round((b.getTime() - a.getTime()) / (24 * 60 * 60 * 1000));
}

function registrationPreview(
  authorName: string,
  authorDistance: string,
  friends: FriendEntry[],
  selectedDistances: string[],
  friendlyYou: string
) {
  const rows: NonNullable<Event["registrations"]> = [];
  const authLabel = authorName.trim() || friendlyYou;
  rows.push({
    id: "pv-a",
    event_id: "preview",
    participant_id: "pv-a",
    participant_display_name: authLabel,
    distances: [
      authorDistance ||
        (selectedDistances[0] ?? "—"),
    ],
    result_time: null,
    result_place: null,
  });
  friends.forEach((f, i) => {
    rows.push({
      id: `pv-f-${i}`,
      event_id: "preview",
      participant_id: `pv-f-${i}`,
      participant_display_name: f.displayName,
      distances: [
        f.distance ||
          selectedDistances[0] ||
          "—",
      ],
      result_time: null,
      result_place: null,
      participant_telegram_username: f.telegramUsername ?? undefined,
    });
  });
  return rows;
}

export function AddEventForm(props: { initialDate?: string } = {}) {
  const { initialDate } = props;
  const router = useRouter();
  const t = useTranslations("addForm");
  const tv = useTranslations("addForm.validation");
  const [sportType, setSportType] = useState<SportType>("running");
  const [name, setName] = useState("");
  const [dateStart, setDateStart] = useState("");
  const [multiDay, setMultiDay] = useState(false);
  const [dateEnd, setDateEnd] = useState("");
  const [dayCount, setDayCount] = useState<number>(2);
  const [location, setLocation] = useState("");
  const [selectedDistances, setSelectedDistances] = useState<string[]>([]);
  const [presetList, setPresetList] = useState<string[]>([]);
  const [customChipOpen, setCustomChipOpen] = useState(false);
  const [customDraft, setCustomDraft] = useState("");
  const [freeDistDraft, setFreeDistDraft] = useState("");
  const [url, setUrl] = useState("");
  const [notes, setNotes] = useState("");
  const [authorName, setAuthorName] = useState("");
  const [authorDistance, setAuthorDistance] = useState("");
  const [friends, setFriends] = useState<FriendEntry[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const isMobile = useIsMobile();
  const [moreOpen, setMoreOpen] = useState(false);

  useLayoutEffect(() => {
    setMoreOpen(!isMobile);
  }, [isMobile]);

  useEffect(() => {
    if (initialDate && /^\d{4}-\d{2}-\d{2}$/.test(initialDate)) {
      setDateStart(initialDate);
    }
  }, [initialDate]);

  const chipsSport = sportType === "running" || sportType === "triathlon";
  const freeDistSport =
    sportType === "swimming" ||
    sportType === "cycling" ||
    sportType === "other";

  const presetFiltered = useMemo(
    () =>
      presetList.filter((d) => d.trim().toLowerCase() !== "other"),
    [presetList]
  );

  useEffect(() => {
    setSelectedDistances([]);
    setCustomChipOpen(false);
    setCustomDraft("");
    setFreeDistDraft("");
  }, [sportType]);

  useEffect(() => {
    if (!chipsSport) {
      setPresetList([]);
      setCustomChipOpen(false);
      setCustomDraft("");
      return;
    }
    let cancel = false;
    void getDistances(sportType)
      .then((d) => {
        if (!cancel) setPresetList(d);
      })
      .catch(() => {
        if (!cancel) setPresetList([]);
      });
    return () => {
      cancel = true;
    };
  }, [sportType, chipsSport]);

  useEffect(() => {
    if (!multiDay || !dateStart) return;
    setDateEnd(addDaysToIso(dateStart, dayCount - 1));
  }, [multiDay, dateStart, dayCount]);

  useEffect(() => {
    if (selectedDistances.length === 0) return;
    setAuthorDistance((prev) =>
      selectedDistances.includes(prev) ? prev : selectedDistances[0]
    );
    setFriends((prev) =>
      prev.map((f) =>
        selectedDistances.includes(f.distance)
          ? f
          : { ...f, distance: selectedDistances[0] }
      )
    );
  }, [selectedDistances]);

  const toggleDistance = useCallback((d: string) => {
    setSelectedDistances((prev) =>
      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]
    );
  }, []);

  function addCustomDistance() {
    const t = customDraft.trim();
    if (!t) return;
    if (!selectedDistances.includes(t)) {
      setSelectedDistances((p) => [...p, t]);
    }
    setCustomDraft("");
    setCustomChipOpen(false);
  }

  function addFreeDistance() {
    const t = freeDistDraft.trim();
    if (!t) return;
    if (!selectedDistances.includes(t)) {
      setSelectedDistances((p) => [...p, t]);
    }
    setFreeDistDraft("");
  }

  const clearForm = () => {
    setSportType("running");
    setName("");
    setDateStart("");
    setMultiDay(false);
    setDateEnd("");
    setDayCount(2);
    setLocation("");
    setSelectedDistances([]);
    setCustomChipOpen(false);
    setCustomDraft("");
    setFreeDistDraft("");
    setUrl("");
    setNotes("");
    setAuthorName("");
    setAuthorDistance("");
    setFriends([]);
    setErrors({});
    setSubmitError(null);
    setSuccess(false);
  };

  const validate = (): boolean => {
    const e: Record<string, string> = {};
    if (!name.trim()) e.name = tv("required");
    else if (name.trim().length > 200) e.name = tv("nameMax");
    if (!dateStart) e.dateStart = tv("required");
    if (!location.trim()) e.location = tv("required");
    if (!authorName.trim()) e.authorName = tv("authorName");
    if (selectedDistances.length === 0) e.distances = tv("distances");
    if (url.trim()) {
      const u = url.trim();
      if (!/^https:\/\//i.test(u) && !/^http:\/\//i.test(u))
        e.url = tv("url");
    }
    if (multiDay) {
      if (!dateEnd) e.dateEnd = tv("dateEndRequired");
      else if (dateEnd < dateStart) e.dateEnd = tv("dateEndBeforeStart");
      else {
        const span = daysBetween(dateStart, dateEnd);
        if (span > 7) e.dateEnd = tv("dateEndMaxWeek");
        if (span < 0) e.dateEnd = tv("dateRangeInvalid");
      }
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const onSubmit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    setSubmitError(null);
    if (!validate()) return;
    setSaving(true);
    try {
      const authorP = await createParticipant({
        display_name: authorName.trim(),
      });

      const friendIds: { id: string; distance: string }[] = [];
      for (const f of friends) {
        if (f.source === "api" && f.participantId) {
          friendIds.push({
            id: f.participantId,
            distance: f.distance || selectedDistances[0],
          });
        } else {
          const pr = await createParticipant({
            display_name: f.displayName.trim(),
          });
          friendIds.push({
            id: pr.id,
            distance: f.distance || selectedDistances[0],
          });
        }
      }

      const eventPayload = {
        name: name.trim().slice(0, 200),
        date_start: dateStart,
        date_end: multiDay ? dateEnd : null,
        location: location.trim(),
        sport_type: sportType,
        url: url.trim() || null,
        notes: notes.trim() || null,
        created_by: authorName.trim(),
      };
      const saved = await createEvent(eventPayload);

      const adist =
        authorDistance && selectedDistances.includes(authorDistance)
          ? authorDistance
          : selectedDistances[0];
      await createRegistration({
        event_id: saved.id,
        participant_id: authorP.id,
        distances: [adist],
      });

      for (const row of friendIds) {
        await createRegistration({
          event_id: saved.id,
          participant_id: row.id,
          distances: [row.distance],
        });
      }

      setSuccess(true);
      setTimeout(() => router.push(`/event/${saved.id}`), 900);
    } catch (err) {
      setSubmitError(
        err instanceof ApiError ? err.message : t("saveFailed")
      );
    } finally {
      setSaving(false);
    }
  };

  const previewEvent: Event = useMemo(
    () => ({
      id: "preview",
      name: name.trim() || t("defaultEventName"),
      date_start: dateStart || dayKey(new Date()),
      date_end: multiDay && dateEnd ? dateEnd : null,
      location: location.trim() || t("defaultLocationLabel"),
      sport_type: sportType,
      url: url.trim() || null,
      notes: notes.trim() || null,
      created_by: authorName.trim() || t("friendlyYou"),
      created_at: new Date().toISOString(),
      registrations: registrationPreview(
        authorName,
        authorDistance,
        friends,
        selectedDistances,
        t("friendlyYou")
      ),
    }),
    [
      name,
      dateStart,
      multiDay,
      dateEnd,
      location,
      sportType,
      url,
      notes,
      authorName,
      authorDistance,
      friends,
      selectedDistances,
      t,
    ]
  );

  const fieldErr = (k: string) =>
    errors[k] ? "border-red-500 focus-visible:ring-red-400" : "";

  const distSectionErr = Boolean(errors.distances);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-slate-900">{t("title")}</h1>

      {success && (
        <div
          className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-green-900"
          role="status"
        >
          {t("successRedirect")}
        </div>
      )}
      {submitError && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-800">
          {submitError}
        </div>
      )}

      <div className="flex flex-col gap-8 lg:flex-row lg:items-start">
        <form
          id="add-event-form"
          className="min-w-0 flex-1 space-y-5 pb-28 lg:max-w-[60%] lg:pb-0"
          onSubmit={onSubmit}
        >
          <div>
            <Label htmlFor="sport">{t("sportType")}</Label>
            <div className="mt-1 flex items-center gap-2">
              <SportIcon sport={sportType} size={22} className="shrink-0" />
              <select
                id="sport"
                value={sportType}
                onChange={(e) =>
                  setSportType(e.target.value as SportType)
                }
                className="min-w-0 flex-1"
              >
                {SPORT_VALUES.map((s) => (
                  <option key={s} value={s}>
                    {t(SPORT_MSG_KEY[s])}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <Label htmlFor="title">
              {t("name")} {t("requiredStar")}
            </Label>
            <Input
              id="title"
              value={name}
              maxLength={200}
              onChange={(e) => setName(e.target.value)}
              className={cn("mt-1", fieldErr("name"))}
              placeholder={t("placeholderEventName")}
            />
            <p className="mt-0.5 text-xs text-slate-500">
              {name.length}/200
            </p>
            {errors.name && (
              <p className="text-sm text-red-600">{errors.name}</p>
            )}
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div>
              <Label htmlFor="ds">
                {t("dateStart")} {t("requiredStar")}
              </Label>
              <Input
                id="ds"
                type="date"
                value={dateStart}
                onChange={(e) => setDateStart(e.target.value)}
                className={cn("mt-1", fieldErr("dateStart"))}
              />
              {errors.dateStart && (
                <p className="text-sm text-red-600">{errors.dateStart}</p>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Label htmlFor="md" className="cursor-pointer">
              {t("multiDay")}
            </Label>
            <Switch
              id="md"
              checked={multiDay}
              onCheckedChange={setMultiDay}
            />
          </div>

          {multiDay && dateStart && (
            <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <div>
                  <Label htmlFor="de">{t("dateEnd")}</Label>
                  <Input
                    id="de"
                    type="date"
                    value={dateEnd}
                    min={dateStart}
                    onChange={(e) => setDateEnd(e.target.value)}
                    className={cn("mt-1", fieldErr("dateEnd"))}
                  />
                  {errors.dateEnd && (
                    <p className="text-sm text-red-600">{errors.dateEnd}</p>
                  )}
                </div>
                <div>
                  <Label htmlFor="dc">{t("days")}</Label>
                  <select
                    id="dc"
                    value={dayCount}
                    onChange={(e) =>
                      setDayCount(Number(e.target.value))
                    }
                    className="mt-1 flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm"
                  >
                    {DAY_OPTIONS.map((n) => (
                      <option key={n} value={n}>
                        {n} {n < 5 ? t("dayWord2") : t("daysWord5")}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-slate-500">
                    {t("multiDayHint")}
                  </p>
                </div>
              </div>
            </div>
          )}

          <div>
            <Label htmlFor="loc">
              {t("locationLabel")} {t("requiredStar")}
            </Label>
            <div className="mt-1">
              <CityAutocomplete
                id="loc"
                value={location}
                onChange={setLocation}
                error={Boolean(errors.location)}
              />
            </div>
            {errors.location && (
              <p className="text-sm text-red-600">{errors.location}</p>
            )}
          </div>

          <div
            className={cn(
              "rounded-lg p-1",
              distSectionErr && "border-2 border-red-400 bg-red-50/50"
            )}
          >
            <Label>
              {t("distanceLabel")} {t("requiredStar")}
            </Label>
            {chipsSport && (
              <>
                <p className="mb-2 mt-1 text-xs text-slate-500">
                  {t("distanceHintChips")}
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  {presetFiltered.map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => toggleDistance(d)}
                      className={cn(
                        "min-h-9 rounded-full border-2 px-3 py-1.5 text-xs font-medium transition-colors",
                        selectedDistances.includes(d)
                          ? "border-sky-600 bg-sky-600 text-white shadow-sm"
                          : "border-slate-300 bg-white text-slate-700 hover:border-slate-400"
                      )}
                    >
                      {selectedDistances.includes(d) ? `✓ ${d}` : d}
                    </button>
                  ))}
                  {!customChipOpen ? (
                    <button
                      type="button"
                      onClick={() => setCustomChipOpen(true)}
                      className={cn(
                        "min-h-9 rounded-full border-2 border-dashed border-slate-400 px-3 py-1.5 text-xs font-medium text-slate-700 hover:border-sky-500 hover:text-sky-800"
                      )}
                    >
                      {t("customChip")}
                    </button>
                  ) : (
                    <span className="inline-flex items-center gap-1">
                      <Input
                        value={customDraft}
                        onChange={(e) => setCustomDraft(e.target.value)}
                        placeholder={t("customDistPlaceholder")}
                        className="h-9 w-36 text-xs sm:w-44"
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            addCustomDistance();
                          }
                          if (e.key === "Escape") {
                            setCustomChipOpen(false);
                            setCustomDraft("");
                          }
                        }}
                        autoFocus
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="h-9"
                        onClick={addCustomDistance}
                      >
                        {t("addButton")}
                      </Button>
                    </span>
                  )}
                </div>
              </>
            )}
            {freeDistSport && (
              <>
                <p className="mb-2 mt-1 text-xs text-slate-500">
                  {t("distanceHintFree")}
                </p>
                <div className="flex flex-wrap gap-2">
                  <Input
                    value={freeDistDraft}
                    onChange={(e) => setFreeDistDraft(e.target.value)}
                    placeholder={t("freeDistPlaceholder")}
                    className="max-w-md flex-1"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addFreeDistance();
                      }
                    }}
                  />
                  <Button type="button" variant="outline" onClick={addFreeDistance}>
                    {t("addButton")}
                  </Button>
                </div>
              </>
            )}
            {errors.distances && (
              <p className="mt-2 text-sm text-red-600">{errors.distances}</p>
            )}
            {selectedDistances.length > 0 && (
              <div className="mt-3 text-sm text-slate-800">
                <span className="font-medium">{t("selectedLabel")} </span>
                <span className="inline-flex flex-wrap items-center gap-2">
                  {selectedDistances.map((d) => (
                    <span
                      key={d}
                      className="inline-flex items-center gap-1 rounded-full border border-emerald-600/40 bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-900"
                    >
                      {d}
                      <button
                        type="button"
                        className="rounded-full px-0.5 hover:bg-emerald-200/60"
                        aria-label={t("removeDistanceAria", { name: d })}
                        onClick={() =>
                          setSelectedDistances((s) =>
                            s.filter((x) => x !== d)
                          )
                        }
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </span>
              </div>
            )}
          </div>

          <ParticipantSelector
            selectedDistances={selectedDistances}
            authorName={authorName}
            onAuthorNameChange={setAuthorName}
            authorDistance={authorDistance}
            onAuthorDistanceChange={setAuthorDistance}
            friends={friends}
            onFriendsChange={setFriends}
            authorError={Boolean(errors.authorName)}
          />
          {errors.authorName && (
            <p className="text-sm text-red-600">{errors.authorName}</p>
          )}

          {isMobile ? (
            <div className="overflow-hidden rounded-lg border border-slate-200 bg-slate-50/80">
              <button
                type="button"
                className="flex min-h-11 w-full items-center justify-between gap-3 px-3 py-2 text-left"
                aria-expanded={moreOpen}
                onClick={() => setMoreOpen((v) => !v)}
              >
                <span className="min-w-0">
                  <span className="block text-sm font-medium text-slate-900">
                    {t("moreSection")}
                  </span>
                  <span className="mt-0.5 block text-xs text-slate-500">
                    {t("moreSectionHint")}
                  </span>
                </span>
                <span className="shrink-0 text-slate-400" aria-hidden>
                  {moreOpen ? "▴" : "▾"}
                </span>
              </button>
              {moreOpen ? (
                <div className="space-y-4 border-t border-slate-200 px-3 pb-4 pt-3">
                  <div>
                    <Label htmlFor="url">{t("urlLabel")}</Label>
                    <Input
                      id="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder={t("urlPlaceholderShort")}
                      className={cn("mt-1", fieldErr("url"))}
                    />
                    {errors.url && (
                      <p className="text-sm text-red-600">{errors.url}</p>
                    )}
                  </div>
                  <div>
                    <Label htmlFor="notes">{t("notesLabel")}</Label>
                    <textarea
                      id="notes"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      rows={4}
                      className="mt-1 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-[var(--color-text-placeholder)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-border-focus)] focus-visible:outline-offset-2"
                      placeholder={t("notesPlaceholderField")}
                    />
                  </div>
                </div>
              ) : null}
            </div>
          ) : (
            <>
              <div>
                <Label htmlFor="url">{t("urlLabel")}</Label>
                <Input
                  id="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder={t("urlPlaceholderShort")}
                  className={cn("mt-1", fieldErr("url"))}
                />
                {errors.url && (
                  <p className="text-sm text-red-600">{errors.url}</p>
                )}
              </div>
              <div>
                <Label htmlFor="notes">{t("notesLabel")}</Label>
                <textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={4}
                  className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-[var(--color-text-placeholder)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-border-focus)] focus-visible:outline-offset-2"
                  placeholder={t("notesPlaceholderField")}
                />
              </div>
            </>
          )}

          <div className="hidden flex-col gap-2 lg:flex lg:flex-row">
            <Button
              type="submit"
              disabled={saving || success}
              className="bg-emerald-600 text-white hover:bg-emerald-700"
            >
              ✅ {t("save")}
            </Button>
            <Button type="button" variant="outline" onClick={clearForm}>
              🔄 {t("clear")}
            </Button>
          </div>
        </form>

        <aside className="hidden w-full lg:sticky lg:top-20 lg:block lg:w-[40%] lg:max-w-md lg:flex-none">
          <h2 className="mb-3 text-lg font-semibold text-slate-900">
            {t("preview")}
          </h2>
          <p className="mb-2 text-xs text-slate-500">
            {t("previewSubtitle")}
          </p>
          <div className="pointer-events-none select-none opacity-95">
            <EventCard event={previewEvent} />
          </div>
        </aside>
      </div>

      {isMobile ? (
        <div
          className="fixed inset-x-0 bottom-0 z-40 flex gap-2 border-t border-[var(--color-border)] bg-[var(--color-surface)]/95 px-4 py-3 backdrop-blur lg:hidden"
          style={{
            paddingBottom: "max(0.75rem, env(safe-area-inset-bottom, 0px))",
          }}
        >
          <Button
            type="submit"
            form="add-event-form"
            disabled={saving || success}
            className="flex-1 bg-emerald-600 text-white hover:bg-emerald-700"
          >
            ✅ {t("save")}
          </Button>
          <Button
            type="button"
            variant="outline"
            className="min-w-0 flex-1"
            onClick={clearForm}
          >
            🔄 {t("clear")}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
