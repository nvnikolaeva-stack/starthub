"use client";

import type {
  Event,
  Participant,
  SimilarEventMatch,
  SportType,
} from "@/lib/types";
import {
  ApiError,
  createEvent,
  createParticipant,
  createRegistration,
  getDistances,
  searchSimilarEvents,
} from "@/lib/api";
import { CityAutocomplete } from "@/components/CityAutocomplete";
import {
  FriendEntry,
  ParticipantSelector,
} from "@/components/ParticipantSelector";
import {
  dayKey,
  formatCompactDayMonthLocalized,
  parseISODate,
} from "@/lib/dates";
import { EventCard } from "@/components/EventCard";
import { SportIcon } from "@/components/SportIcon";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";
import { useIsMobile } from "@/hooks/use-is-mobile";
import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
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
  const locale = useLocale();
  const t = useTranslations("addForm");
  const te = useTranslations("event");
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
  const [authorParticipantId, setAuthorParticipantId] = useState<string | null>(
    null
  );
  const [authorDistance, setAuthorDistance] = useState("");
  const [friends, setFriends] = useState<FriendEntry[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const isMobile = useIsMobile();
  const [moreOpen, setMoreOpen] = useState(false);
  const [nameSimilar, setNameSimilar] = useState<SimilarEventMatch[]>([]);
  const [dateSimilarExact, setDateSimilarExact] = useState<
    SimilarEventMatch[]
  >([]);
  const [dateSimilarRest, setDateSimilarRest] = useState<SimilarEventMatch[]>(
    []
  );
  const [dateSimilarOpen, setDateSimilarOpen] = useState(false);
  const [exactDupMatches, setExactDupMatches] = useState<SimilarEventMatch[]>(
    []
  );
  const [dupForceCreate, setDupForceCreate] = useState(false);
  const [joinModalEvent, setJoinModalEvent] = useState<SimilarEventMatch | null>(
    null
  );
  const [joinName, setJoinName] = useState("");
  const [joinDistOptions, setJoinDistOptions] = useState<string[]>([]);
  const [joinDistance, setJoinDistance] = useState("");
  const [joinBusy, setJoinBusy] = useState(false);

  useLayoutEffect(() => {
    setMoreOpen(!isMobile);
  }, [isMobile]);

  useEffect(() => {
    if (initialDate && /^\d{4}-\d{2}-\d{2}$/.test(initialDate)) {
      setDateStart(initialDate);
    }
  }, [initialDate]);

  useEffect(() => {
    const q = name.trim();
    if (q.length < 3) {
      setNameSimilar([]);
      return;
    }
    let dead = false;
    const tid = setTimeout(() => {
      void searchSimilarEvents({ name: q })
        .then((r) => {
          if (dead) return;
          setNameSimilar(r.exact_matches ?? []);
        })
        .catch(() => {
          if (!dead) setNameSimilar([]);
        });
    }, 300);
    return () => {
      dead = true;
      clearTimeout(tid);
    };
  }, [name]);

  useEffect(() => {
    if (!dateStart || !/^\d{4}-\d{2}-\d{2}$/.test(dateStart)) {
      setDateSimilarExact([]);
      setDateSimilarRest([]);
      setDateSimilarOpen(false);
      return;
    }
    let dead = false;
    void searchSimilarEvents({ date: dateStart })
      .then((r) => {
        if (dead) return;
        const ex = r.exact_matches ?? [];
        const dm = r.date_matches ?? [];
        setDateSimilarExact(ex);
        setDateSimilarRest(dm);
        if (!ex.length && !dm.length) setDateSimilarOpen(false);
      })
      .catch(() => {
        if (!dead) {
          setDateSimilarExact([]);
          setDateSimilarRest([]);
        }
      });
    return () => {
      dead = true;
    };
  }, [dateStart]);

  useEffect(() => {
    setDupForceCreate(false);
  }, [name, dateStart]);

  useEffect(() => {
    const q = name.trim();
    if (q.length < 3 || !dateStart || !/^\d{4}-\d{2}-\d{2}$/.test(dateStart)) {
      setExactDupMatches([]);
      return;
    }
    let dead = false;
    void searchSimilarEvents({ name: q, date: dateStart })
      .then((r) => {
        if (dead) return;
        setExactDupMatches(r.exact_matches ?? []);
      })
      .catch(() => {
        if (!dead) setExactDupMatches([]);
      });
    return () => {
      dead = true;
    };
  }, [name, dateStart]);

  useEffect(() => {
    if (!joinModalEvent) return;
    setJoinName((prev) => prev || authorName.trim());
    let c = false;
    void getDistances(String(joinModalEvent.sport_type))
      .then((list) => {
        if (c) return;
        setJoinDistOptions(list);
        setJoinDistance((d) => (list.includes(d) ? d : list[0] ?? ""));
      })
      .catch(() => {
        if (!c) {
          setJoinDistOptions([]);
          setJoinDistance("");
        }
      });
    return () => {
      c = true;
    };
  }, [joinModalEvent, authorName]);

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

  const handleAuthorNameInput = useCallback((v: string) => {
    setAuthorName(v);
    setAuthorParticipantId(null);
  }, []);

  const onPickParticipantAsAuthor = useCallback((p: Participant) => {
    setAuthorName(p.display_name);
    setAuthorParticipantId(p.id);
    setFriends((prev) => prev.filter((f) => f.participantId !== p.id));
  }, []);

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
    setAuthorParticipantId(null);
    setAuthorDistance("");
    setFriends([]);
    setErrors({});
    setSubmitError(null);
    setSuccess(false);
    setNameSimilar([]);
    setDateSimilarExact([]);
    setDateSimilarRest([]);
    setDateSimilarOpen(false);
    setExactDupMatches([]);
    setDupForceCreate(false);
    setJoinModalEvent(null);
    setJoinName("");
    setJoinDistOptions([]);
    setJoinDistance("");
  };

  const formatEvDate = (iso: string) =>
    formatCompactDayMonthLocalized(parseISODate(iso), locale);

  const dateHintEvents = useMemo(() => {
    const seen = new Set<string>();
    const out: SimilarEventMatch[] = [];
    for (const ev of dateSimilarExact) {
      if (!seen.has(ev.id)) {
        seen.add(ev.id);
        out.push(ev);
      }
    }
    for (const ev of dateSimilarRest) {
      if (!seen.has(ev.id)) {
        seen.add(ev.id);
        out.push(ev);
      }
    }
    return out;
  }, [dateSimilarExact, dateSimilarRest]);

  const submitJoinSimilar = async () => {
    if (!joinModalEvent || !joinName.trim() || !joinDistance) return;
    const targetId = joinModalEvent.id;
    setJoinBusy(true);
    setSubmitError(null);
    try {
      const p = await createParticipant({
        display_name: joinName.trim(),
      });
      await createRegistration({
        event_id: targetId,
        participant_id: p.id,
        distances: [joinDistance.trim()],
      });
      setJoinModalEvent(null);
      setSuccess(true);
      setTimeout(() => router.push(`/event/${targetId}`), 600);
    } catch (err) {
      setSubmitError(
        err instanceof ApiError ? err.message : t("saveFailed")
      );
    } finally {
      setJoinBusy(false);
    }
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
      const authorNorm = authorName.trim().toLowerCase();
      let authorId: string;
      if (authorParticipantId) {
        authorId = authorParticipantId;
      } else {
        const matchFriend = friends.find(
          (f) =>
            f.source === "api" &&
            f.participantId &&
            f.displayName.trim().toLowerCase() === authorNorm
        );
        if (matchFriend?.participantId) {
          authorId = matchFriend.participantId;
        } else {
          const ap = await createParticipant({
            display_name: authorName.trim(),
          });
          authorId = ap.id;
        }
      }

      const usedIds = new Set<string>([authorId]);
      const usedNames = new Set<string>([authorNorm]);

      const friendRegs: { id: string; distance: string }[] = [];
      for (const f of friends) {
        if (f.source === "api" && f.participantId) {
          if (usedIds.has(f.participantId)) continue;
          const fn = f.displayName.trim().toLowerCase();
          if (usedNames.has(fn)) continue;
          usedIds.add(f.participantId);
          usedNames.add(fn);
          friendRegs.push({
            id: f.participantId,
            distance: f.distance || selectedDistances[0] || "",
          });
        } else {
          const fn = f.displayName.trim().toLowerCase();
          if (usedNames.has(fn)) continue;
          usedNames.add(fn);
          const pr = await createParticipant({
            display_name: f.displayName.trim(),
          });
          usedIds.add(pr.id);
          friendRegs.push({
            id: pr.id,
            distance: f.distance || selectedDistances[0] || "",
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
      const saved = await createEvent(eventPayload, {
        forceDuplicate: dupForceCreate && exactDupMatches.length > 0,
      });

      const adist =
        authorDistance && selectedDistances.includes(authorDistance)
          ? authorDistance
          : selectedDistances[0];
      await createRegistration({
        event_id: saved.id,
        participant_id: authorId,
        distances: [adist],
      });

      for (const row of friendRegs) {
        await createRegistration({
          event_id: saved.id,
          participant_id: row.id,
          distances: [row.distance],
        });
      }

      setSuccess(true);
      setTimeout(() => router.push(`/event/${saved.id}`), 900);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setSubmitError(t("duplicate409Hint"));
      } else {
        setSubmitError(
          err instanceof ApiError ? err.message : t("saveFailed")
        );
      }
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
          <style>{`@keyframes addSimilarIn{from{opacity:0}to{opacity:1}}`}</style>
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
            {nameSimilar.length > 0 ? (
              <div
                className="mt-3 w-full space-y-3 rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface-tinted)] p-3 transition-opacity duration-200 sm:p-4"
                style={{ animation: "addSimilarIn 0.2s ease-out" }}
              >
                <p className="text-sm font-medium text-[var(--color-text)]">
                  📌 {t("similarNameTitle")}
                </p>
                <div className="space-y-2">
                  {nameSimilar.map((ev) => (
                    <div
                      key={ev.id}
                      className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-3 shadow-sm"
                    >
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <div className="min-w-0">
                          <p className="font-medium text-[var(--color-text)]">
                            {ev.name}
                          </p>
                          <p className="text-xs text-[var(--color-text-muted)]">
                            {formatEvDate(ev.date_start)} • {ev.location} •{" "}
                            {te("participantsCountInline", {
                              count: ev.participants_count,
                            })}
                          </p>
                        </div>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="shrink-0"
                          onClick={() => setJoinModalEvent(ev)}
                        >
                          {t("similarJoin")}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-[var(--color-text-muted)]">
                  {t("similarContinueCreate")}
                </p>
              </div>
            ) : null}
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

          {dateHintEvents.length > 0 ? (
            <div
              className="w-full space-y-3 rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface-tinted)] p-3 transition-opacity duration-200 sm:p-4"
              style={{ animation: "addSimilarIn 0.2s ease-out" }}
            >
              <p className="text-sm font-medium text-[var(--color-text)]">
                📅 {t("similarDateTitle")}
              </p>
              {!dateSimilarOpen ? (
                <ul className="list-inside list-disc space-y-1 text-sm text-[var(--color-text)]">
                  {dateHintEvents.map((ev) => (
                    <li key={ev.id}>
                      <span className="font-medium">{ev.name}</span> (
                      {SPORT_VALUES.includes(ev.sport_type as SportType)
                        ? t(SPORT_MSG_KEY[ev.sport_type as SportType])
                        : ev.sport_type}
                      ,{" "}
                      {te("participantsCountInline", {
                        count: ev.participants_count,
                      })}
                      )
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="space-y-2">
                  {dateHintEvents.map((ev) => (
                    <div
                      key={ev.id}
                      className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-3 shadow-sm"
                    >
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <div className="min-w-0">
                          <p className="font-medium">{ev.name}</p>
                          <p className="text-xs text-[var(--color-text-muted)]">
                            {formatEvDate(ev.date_start)} • {ev.location} •{" "}
                            {te("participantsCountInline", {
                              count: ev.participants_count,
                            })}
                          </p>
                        </div>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="shrink-0"
                          onClick={() => setJoinModalEvent(ev)}
                        >
                          {t("similarJoin")}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="w-full sm:w-auto"
                onClick={() => setDateSimilarOpen((o) => !o)}
              >
                {dateSimilarOpen
                  ? t("similarPickCollapse")
                  : t("similarPickExpand")}
              </Button>
            </div>
          ) : null}

          {!dupForceCreate && exactDupMatches.length > 0 ? (
            <div
              className="space-y-3 rounded-[var(--radius-lg)] border-2 border-amber-400 bg-amber-50/95 p-4 text-amber-950 shadow-sm transition-opacity duration-200 dark:border-amber-500/70 dark:bg-amber-950/40 dark:text-amber-50"
              style={{ animation: "addSimilarIn 0.2s ease-out" }}
            >
              <p className="text-sm font-semibold">⚠️ {t("similarExactTitle")}</p>
              {exactDupMatches.slice(0, 3).map((ev) => (
                <div key={ev.id}>
                  <p className="text-sm">
                    <span className="font-medium">{ev.name}</span> •{" "}
                    {formatEvDate(ev.date_start)} • {ev.location}
                  </p>
                  <p className="text-xs text-amber-900/80 dark:text-amber-100/80">
                    {ev.participants.slice(0, 8).join(", ")}
                    {ev.participants.length > 8
                      ? ` (+${ev.participants.length - 8})`
                      : ""}{" "}
                    ({ev.participants_count})
                  </p>
                </div>
              ))}
              <div className="flex flex-col gap-2 sm:flex-row">
                <Button
                  type="button"
                  className="bg-amber-600 text-white hover:bg-amber-700"
                  onClick={() => setJoinModalEvent(exactDupMatches[0])}
                >
                  {t("similarJoinThis")}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="border-amber-600 text-amber-950 hover:bg-amber-100 dark:border-amber-400 dark:text-amber-50 dark:hover:bg-amber-900/50"
                  onClick={() => setDupForceCreate(true)}
                >
                  {t("similarCreateAnyway")}
                </Button>
              </div>
            </div>
          ) : null}

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
            onAuthorNameChange={handleAuthorNameInput}
            authorParticipantId={authorParticipantId}
            onPickParticipantAsAuthor={onPickParticipantAsAuthor}
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

          <div className="hidden items-center justify-between gap-4 lg:flex">
            <Button
              type="button"
              variant="ghost"
              className="min-h-11 text-[var(--color-text-secondary)] hover:text-[var(--color-text)]"
              onClick={clearForm}
            >
              {t("clear")}
            </Button>
            <Button
              type="submit"
              disabled={saving || success}
              className="min-h-11 bg-[var(--color-accent)] text-[var(--color-accent-text)] hover:bg-[var(--color-accent-hover)]"
            >
              ✅ {t("save")}
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
          className="fixed inset-x-0 bottom-0 z-40 flex justify-between gap-3 border-t border-[var(--color-border)] bg-[var(--color-surface)]/95 px-4 py-3 backdrop-blur lg:hidden"
          style={{
            paddingBottom: "max(0.75rem, env(safe-area-inset-bottom, 0px))",
          }}
        >
          <Button
            type="button"
            variant="ghost"
            className="min-h-11 shrink-0 text-[var(--color-text-secondary)]"
            onClick={clearForm}
          >
            {t("clear")}
          </Button>
          <Button
            type="submit"
            form="add-event-form"
            disabled={saving || success}
            className="min-h-11 min-w-[10rem] flex-1 bg-[var(--color-accent)] text-[var(--color-accent-text)] hover:bg-[var(--color-accent-hover)] sm:max-w-md sm:flex-none"
          >
            ✅ {t("save")}
          </Button>
        </div>
      ) : null}

      <Dialog
        open={joinModalEvent !== null}
        onOpenChange={(open) => {
          if (!open) setJoinModalEvent(null);
        }}
        title={t("joinModalTitle")}
      >
        {joinModalEvent ? (
          <div className="space-y-4">
            <div>
              <Label htmlFor="join-n">{t("joinModalName")}</Label>
              <Input
                id="join-n"
                value={joinName}
                onChange={(e) => setJoinName(e.target.value)}
                className="mt-1"
                autoComplete="name"
              />
            </div>
            <div>
              <Label htmlFor="join-d">{t("joinModalDistance")}</Label>
              {joinDistOptions.length > 0 ? (
                <select
                  id="join-d"
                  value={joinDistance}
                  onChange={(e) => setJoinDistance(e.target.value)}
                  className="mt-1 flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm"
                >
                  {joinDistOptions.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              ) : (
                <Input
                  id="join-d"
                  value={joinDistance}
                  onChange={(e) => setJoinDistance(e.target.value)}
                  className="mt-1"
                  placeholder={t("freeDistPlaceholder")}
                />
              )}
            </div>
            <Button
              type="button"
              className="w-full bg-sky-600 text-white hover:bg-sky-700"
              disabled={joinBusy || !joinName.trim() || !joinDistance.trim()}
              onClick={() => void submitJoinSimilar()}
            >
              {t("joinModalSubmit")}
            </Button>
          </div>
        ) : null}
      </Dialog>
    </div>
  );
}
