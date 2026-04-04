"use client";

import type { Event, Registration, SportType } from "@/lib/types";
import {
  ApiError,
  createParticipant,
  createRegistration,
  deleteEvent,
  getDistances,
  getEvent,
  getEventIcal,
  updateEvent,
} from "@/lib/api";
import { formatEventRangeLocalized } from "@/lib/dates";
import { SPORT_BORDER } from "@/lib/sport";
import { SportIcon } from "@/components/SportIcon";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, Pencil } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

const SPORT_OPTIONS: SportType[] = [
  "swimming",
  "triathlon",
  "running",
  "cycling",
  "other",
];

function eventExternalUrl(raw: string): string {
  const u = raw.trim();
  if (!u) return "";
  return /^https?:\/\//i.test(u) ? u : `https://${u}`;
}

function registrationHostname(raw: string): string {
  try {
    return new URL(eventExternalUrl(raw)).hostname;
  } catch {
    return raw.replace(/^https?:\/\//i, "").split("/")[0] || raw;
  }
}

function regTelegram(r: Registration): string | null {
  if (r.participant_telegram_username)
    return `@${r.participant_telegram_username}`;
  if (r.participant?.telegram_username)
    return `@${r.participant.telegram_username}`;
  return null;
}

export function EventCardFull({ eventId }: { eventId: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const openedEditFromQuery = useRef(false);
  const locale = useLocale();
  const t = useTranslations("event");
  const tf = useTranslations("filters");
  const tCommon = useTranslations("common");

  const regDisplayName = (r: Registration) =>
    r.participant_display_name ||
    r.participant?.display_name ||
    t("defaultParticipant");

  const [event, setEvent] = useState<Event | null>(null);
  const [loadState, setLoadState] = useState<"loading" | "ok" | "err">(
    "loading"
  );
  const [errMsg, setErrMsg] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setErrMsg(null);
    try {
      const e = await getEvent(eventId);
      setEvent(e);
      setLoadState("ok");
    } catch (e) {
      setLoadState("err");
      setErrMsg(e instanceof ApiError ? e.message : tCommon("serverError"));
    }
  }, [eventId, tCommon]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const [joinOpen, setJoinOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [delOpen, setDelOpen] = useState(false);

  const [joinName, setJoinName] = useState("");
  const [joinDistances, setJoinDistances] = useState<string[]>([]);
  const [joinCustom, setJoinCustom] = useState("");
  const [presetDists, setPresetDists] = useState<string[]>([]);
  const [joinBusy, setJoinBusy] = useState(false);

  const [editForm, setEditForm] = useState({
    name: "",
    date_start: "",
    date_end: "",
    location: "",
    sport_type: "running" as SportType,
    url: "",
    notes: "",
    created_by: "",
  });
  const [editBusy, setEditBusy] = useState(false);

  const [delBusy, setDelBusy] = useState(false);
  const [saveToast, setSaveToast] = useState(false);

  useEffect(() => {
    if (!joinOpen || !event) return;
    setJoinName("");
    setJoinDistances([]);
    setJoinCustom("");
    void getDistances(event.sport_type)
      .then((rows) =>
        setPresetDists(
          rows.filter((d) => d.trim().toLowerCase() !== "other")
        )
      )
      .catch(() => setPresetDists([]));
  }, [joinOpen, event]);

  useEffect(() => {
    if (openedEditFromQuery.current) return;
    if (searchParams.get("edit") !== "true") return;
    if (loadState !== "ok" || !event) return;
    openedEditFromQuery.current = true;
    setEditOpen(true);
  }, [searchParams, loadState, event]);

  useEffect(() => {
    if (!event || loadState !== "ok" || !editOpen) return;
    setEditForm({
      name: event.name,
      date_start: event.date_start.slice(0, 10),
      date_end: event.date_end ? event.date_end.slice(0, 10) : "",
      location: event.location,
      sport_type: event.sport_type,
      url: event.url || "",
      notes: event.notes || "",
      created_by: event.created_by,
    });
  }, [editOpen, event, loadState]);

  async function downloadIcs() {
    if (!event) return;
    try {
      const blob = await getEventIcal(event.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "event.ics";
      a.rel = "noopener";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setErrMsg(
        e instanceof ApiError ? e.message : t("downloadCalendarFailed")
      );
    }
  }

  async function submitJoin() {
    if (!event || !joinName.trim()) return;
    const dists =
      joinDistances.length > 0
        ? joinDistances
        : joinCustom.trim()
          ? [joinCustom.trim()]
          : null;
    if (!dists?.length) {
      setErrMsg(t("joinNeedDistance"));
      return;
    }
    setJoinBusy(true);
    setErrMsg(null);
    try {
      const p = await createParticipant({ display_name: joinName.trim() });
      await createRegistration({
        event_id: event.id,
        participant_id: p.id,
        distances: dists,
      });
      setJoinOpen(false);
      await reload();
    } catch (e) {
      setErrMsg(e instanceof ApiError ? e.message : tCommon("serverError"));
    } finally {
      setJoinBusy(false);
    }
  }

  async function submitEdit() {
    if (!event) return;
    setEditBusy(true);
    setErrMsg(null);
    try {
      await updateEvent(event.id, {
        name: editForm.name,
        date_start: editForm.date_start,
        date_end: editForm.date_end || null,
        location: editForm.location,
        sport_type: editForm.sport_type,
        url: editForm.url || null,
        notes: editForm.notes || null,
        created_by: editForm.created_by,
      });
      setEditOpen(false);
      setSaveToast(true);
      await reload();
      window.setTimeout(() => {
        setSaveToast(false);
        router.push("/");
      }, 1500);
    } catch (e) {
      setErrMsg(e instanceof ApiError ? e.message : tCommon("serverError"));
    } finally {
      setEditBusy(false);
    }
  }

  async function confirmDelete() {
    if (!event) return;
    setDelBusy(true);
    setErrMsg(null);
    try {
      await deleteEvent(event.id);
      setDelOpen(false);
      router.push("/");
    } catch (e) {
      setErrMsg(e instanceof ApiError ? e.message : tCommon("serverError"));
    } finally {
      setDelBusy(false);
    }
  }

  function toggleJoinDistance(d: string) {
    setJoinDistances((prev) =>
      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]
    );
  }

  if (loadState === "loading") {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <p className="text-slate-600">{t("loading")}</p>
      </div>
    );
  }

  if (loadState === "err" || !event) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <p className="text-red-700">{errMsg || t("notFound")}</p>
        <Button className="mt-4" variant="outline" onClick={() => router.push("/")}>
          {t("home")}
        </Button>
      </div>
    );
  }

  const regs = event.registrations || [];
  const distSummary =
    regs.length > 0
      ? [...new Set(regs.flatMap((r) => r.distances || []).filter(Boolean))].join(
          ", "
        )
      : "";

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      {saveToast ? (
        <div
          role="status"
          className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-lg border border-slate-200 bg-slate-900 px-4 py-2.5 text-sm text-white shadow-lg"
        >
          Старт сохранён!
        </div>
      ) : null}
      {errMsg && (
        <div
          className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900"
          role="alert"
        >
          {errMsg}
        </div>
      )}
      <Card
        className={cn(
          "overflow-hidden border-l-4",
          SPORT_BORDER[event.sport_type]
        )}
      >
        <div className="space-y-4 p-5 sm:p-6">
          <button
            type="button"
            onClick={() => router.push("/")}
            className="mb-1 inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft size={16} aria-hidden />
            К календарю
          </button>
          <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-slate-500">
            <SportIcon sport={event.sport_type} className="shrink-0" />
            {tf(event.sport_type).toUpperCase()}
          </p>
          <h1 className="text-2xl font-bold text-slate-900">{event.name}</h1>
          <ul className="space-y-2 text-sm text-slate-700">
            <li>
              <span aria-hidden>📅 </span>
              {formatEventRangeLocalized(
                event.date_start,
                event.date_end,
                locale
              )}
            </li>
            <li>
              <span aria-hidden>📍 </span>
              {event.location}
            </li>
            {distSummary ? (
              <li>
                <span aria-hidden>📏 </span>
                {distSummary}
              </li>
            ) : null}
            {event.url ? (
              <li>
                <a
                  href={eventExternalUrl(event.url)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 break-all text-sky-700 underline hover:text-sky-900"
                >
                  <span aria-hidden>🔗</span>
                  <span>
                    {t("registrationLink")}: {registrationHostname(event.url)}{" "}
                    →
                  </span>
                </a>
              </li>
            ) : null}
            {event.notes ? (
              <li>
                <span aria-hidden>📝 </span>
                {event.notes}
              </li>
            ) : null}
          </ul>

          <div>
            <h2 className="mb-2 text-sm font-semibold text-slate-900">
              {t("participantsCount", { count: regs.length })}
            </h2>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
              {regs.length === 0 ? (
                <p className="text-slate-600">{t("noRegistrationsYet")}</p>
              ) : (
                <ul className="space-y-3">
                  {regs.map((r) => {
                    const tg = regTelegram(r);
                    const dist = (r.distances || []).join(", ") || t("dash");
                    const time = r.result_time || null;
                    const place = r.result_place || null;
                    return (
                      <li key={r.id} className="border-b border-slate-200 pb-3 last:border-0 last:pb-0">
                        <div className="font-medium text-slate-900">
                          {regDisplayName(r)}
                          {tg ? (
                            <span className="text-slate-600"> ({tg})</span>
                          ) : null}
                        </div>
                        <div className="mt-1 text-slate-600">
                          {dist}
                          {time
                            ? t("resultsLine", { time })
                            : ` — ${t("noResult")}`}
                          {place ? t("placeLine", { place }) : ""}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>

          <div className="mt-4 flex w-full flex-col flex-wrap gap-2 sm:flex-row">
            <Button
              type="button"
              variant="outline"
              className="min-h-[44px] w-full min-w-0 whitespace-normal break-words sm:flex-1 sm:min-w-[140px] sm:max-w-full"
              onClick={() => void downloadIcs()}
            >
              📅 {t("addToCalendar")}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="inline-flex min-h-[44px] w-full min-w-0 items-center justify-center gap-2 whitespace-normal break-words px-4 py-2.5 sm:flex-1 sm:min-w-[140px] sm:max-w-full"
              onClick={() => setEditOpen(true)}
            >
              <Pencil size={16} aria-hidden />
              <span>{t("edit")}</span>
            </Button>
            <Button
              type="button"
              className="min-h-[44px] w-full min-w-0 whitespace-normal break-words sm:flex-1 sm:min-w-[140px] sm:max-w-full"
              onClick={() => setJoinOpen(true)}
            >
              👥 {t("joinEvent")}
            </Button>
            <Button
              type="button"
              variant="destructive"
              className="min-h-[44px] w-full min-w-0 whitespace-normal break-words sm:flex-1 sm:min-w-[140px] sm:max-w-full"
              onClick={() => setDelOpen(true)}
            >
              🗑 {t("delete")}
            </Button>
          </div>
        </div>
      </Card>

      <Dialog open={joinOpen} onOpenChange={setJoinOpen} title={t("joinDialogTitle")}>
        <div className="space-y-4">
          <div>
            <Label htmlFor="join-name">{t("joinName")}</Label>
            <Input
              id="join-name"
              className="mt-1"
              value={joinName}
              onChange={(e) => setJoinName(e.target.value)}
              placeholder={t("joinNamePlaceholder")}
            />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-900">{t("joinDistances")}</p>
            {presetDists.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {presetDists.map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => toggleJoinDistance(d)}
                    className={cn(
                      "rounded-full border px-3 py-1 text-xs font-medium",
                      joinDistances.includes(d)
                        ? "border-slate-900 bg-slate-900 text-white"
                        : "border-slate-300 bg-white text-slate-800"
                    )}
                  >
                    {d}
                  </button>
                ))}
              </div>
            )}
            <Label htmlFor="join-custom" className="mt-3 block">
              {t("joinCustomDistance")}
            </Label>
            <Input
              id="join-custom"
              className="mt-1"
              value={joinCustom}
              onChange={(e) => setJoinCustom(e.target.value)}
              placeholder={t("joinCustomPlaceholder")}
            />
          </div>
          <Button
            type="button"
            className="w-full sm:w-auto"
            disabled={joinBusy || !joinName.trim()}
            onClick={() => void submitJoin()}
          >
            {joinBusy ? t("joinSaving") : t("joinSubmit")}
          </Button>
        </div>
      </Dialog>

      <Dialog open={editOpen} onOpenChange={setEditOpen} title={t("editDialogTitle")}>
        <div className="grid gap-3">
          <div>
            <Label htmlFor="ef-name">{t("labelName")}</Label>
            <Input
              id="ef-name"
              className="mt-1"
              value={editForm.name}
              onChange={(e) =>
                setEditForm((f) => ({ ...f, name: e.target.value }))
              }
            />
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            <div>
              <Label htmlFor="ef-start">{t("labelDateStart")}</Label>
              <Input
                id="ef-start"
                type="date"
                className="mt-1"
                value={editForm.date_start}
                onChange={(e) =>
                  setEditForm((f) => ({ ...f, date_start: e.target.value }))
                }
              />
            </div>
            <div>
              <Label htmlFor="ef-end">{t("labelDateEnd")}</Label>
              <Input
                id="ef-end"
                type="date"
                className="mt-1"
                value={editForm.date_end}
                onChange={(e) =>
                  setEditForm((f) => ({ ...f, date_end: e.target.value }))
                }
              />
            </div>
          </div>
          <div>
            <Label htmlFor="ef-loc">{t("labelLocation")}</Label>
            <Input
              id="ef-loc"
              className="mt-1"
              value={editForm.location}
              onChange={(e) =>
                setEditForm((f) => ({ ...f, location: e.target.value }))
              }
            />
          </div>
          <div>
            <Label htmlFor="ef-sport">{t("labelSport")}</Label>
            <select
              id="ef-sport"
              className="mt-1 flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm"
              value={editForm.sport_type}
              onChange={(e) =>
                setEditForm((f) => ({
                  ...f,
                  sport_type: e.target.value as SportType,
                }))
              }
            >
              {SPORT_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {tf(s)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="ef-url">{t("labelUrl")}</Label>
            <Input
              id="ef-url"
              className="mt-1"
              value={editForm.url}
              onChange={(e) =>
                setEditForm((f) => ({ ...f, url: e.target.value }))
              }
            />
          </div>
          <div>
            <Label htmlFor="ef-notes">{t("labelNotes")}</Label>
            <Input
              id="ef-notes"
              className="mt-1"
              value={editForm.notes}
              onChange={(e) =>
                setEditForm((f) => ({ ...f, notes: e.target.value }))
              }
            />
          </div>
          <div>
            <Label htmlFor="ef-by">{t("labelCreatedBy")}</Label>
            <Input
              id="ef-by"
              className="mt-1"
              value={editForm.created_by}
              onChange={(e) =>
                setEditForm((f) => ({ ...f, created_by: e.target.value }))
              }
            />
          </div>
          <Button
            type="button"
            disabled={editBusy}
            onClick={() => void submitEdit()}
          >
            {editBusy ? t("saving") : t("save")}
          </Button>
        </div>
      </Dialog>

      <Dialog open={delOpen} onOpenChange={setDelOpen} title={t("deleteDialogTitle")}>
        <p className="mb-4 text-sm text-slate-700">
          {t("confirmDelete", { count: regs.length })}
        </p>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Button type="button" variant="outline" onClick={() => setDelOpen(false)}>
            {tCommon("cancel")}
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={delBusy}
            onClick={() => void confirmDelete()}
          >
            {delBusy ? t("deleting") : t("deleteSubmit")}
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
