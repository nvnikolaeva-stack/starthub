"use client";

import type {
  CommunityStats,
  Participant,
  ParticipantDetail,
  ParticipantStats,
  SportType,
} from "@/lib/types";
import {
  ApiError,
  getCommunityStats,
  getParticipant,
  getParticipantStats,
  listParticipants,
} from "@/lib/api";
import { SPORT_DOT } from "@/lib/sport";
import { SportIcon } from "@/components/SportIcon";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function isSportType(s: string): s is SportType {
  return (
    s === "swimming" ||
    s === "running" ||
    s === "cycling" ||
    s === "triathlon" ||
    s === "other"
  );
}

const sportFill = (s: string) =>
  isSportType(s) ? SPORT_DOT[s] : "var(--sport-other)";

export function StatsPageContent() {
  const t = useTranslations("stats");
  const tf = useTranslations("filters");
  const tc = useTranslations("common");

  const sportLabelLocalized = useCallback(
    (s: string) => (isSportType(s) ? tf(s) : s),
    [tf]
  );

  const [tab, setTab] = useState<"team" | "people">("team");
  const [community, setCommunity] = useState<CommunityStats | null>(null);
  const [commErr, setCommErr] = useState<string | null>(null);
  const [loadingComm, setLoadingComm] = useState(true);

  const [participants, setParticipants] = useState<Participant[]>([]);
  const [statsById, setStatsById] = useState<
    Record<string, ParticipantStats | null>
  >({});
  const [detailById, setDetailById] = useState<
    Record<string, ParticipantDetail | null>
  >({});
  const [detailLoading, setDetailLoading] = useState<Record<string, boolean>>(
    {}
  );
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [loadingPeople, setLoadingPeople] = useState(false);
  const [peopleErr, setPeopleErr] = useState<string | null>(null);

  useEffect(() => {
    let c = false;
    setLoadingComm(true);
    void getCommunityStats()
      .then((d) => {
        if (!c) {
          setCommunity(d);
          setCommErr(null);
        }
      })
      .catch((e) => {
        if (!c)
          setCommErr(
            e instanceof ApiError ? e.message : t("loadFailed")
          );
      })
      .finally(() => {
        if (!c) setLoadingComm(false);
      });
    return () => {
      c = true;
    };
  }, [t]);

  useEffect(() => {
    if (tab !== "people") return;
    let c = false;
    setLoadingPeople(true);
    setPeopleErr(null);
    void (async () => {
      try {
        const list = await listParticipants();
        if (c) return;
        setParticipants(list);
        const entries = await Promise.all(
          list.map(async (p) => {
            try {
              const s = await getParticipantStats(p.id);
              return [p.id, s] as const;
            } catch {
              return [p.id, null] as const;
            }
          })
        );
        if (c) return;
        const map: Record<string, ParticipantStats | null> = {};
        for (const [id, s] of entries) map[id] = s;
        setStatsById(map);
      } catch (e) {
        if (!c)
          setPeopleErr(
            e instanceof ApiError ? e.message : tc("serverError")
          );
      } finally {
        if (!c) setLoadingPeople(false);
      }
    })();
    return () => {
      c = true;
    };
  }, [tab, tc]);

  const sortedParticipants = useMemo(() => {
    return [...participants].sort((a, b) => {
      const ta = statsById[a.id]?.total_events ?? 0;
      const tb = statsById[b.id]?.total_events ?? 0;
      return tb - ta;
    });
  }, [participants, statsById]);

  const sportBars = useMemo(() => {
    if (!community) return [];
    return [...community.popular_sports]
      .map((row) => {
        const st = row.sport_type || row.sport || "other";
        return {
          key: st,
          name: sportLabelLocalized(st),
          value: row.count,
        };
      })
      .sort((a, b) => b.value - a.value);
  }, [community, sportLabelLocalized]);

  const maxSportCount = useMemo(
    () => Math.max(1, ...sportBars.map((s) => s.value)),
    [sportBars]
  );

  const barData = useMemo(() => {
    if (!community) return [];
    return community.popular_locations.map((r) => ({
      location: r.location.length > 24 ? `${r.location.slice(0, 24)}…` : r.location,
      full: r.location,
      count: r.count,
    }));
  }, [community]);

  const barChartHeight = useMemo(
    () => Math.max(200, barData.length * 32),
    [barData.length]
  );
  const locationsChartHeight = Math.min(barChartHeight, 360);

  const toggleDetail = useCallback(async (id: string) => {
    let opening = false;
    setExpanded((e) => {
      const next = !e[id];
      opening = next;
      return { ...e, [id]: next };
    });
    if (!opening) return;
    if (Object.prototype.hasOwnProperty.call(detailById, id)) return;
    setDetailLoading((m) => ({ ...m, [id]: true }));
    try {
      const d = await getParticipant(id);
      setDetailById((m) => ({ ...m, [id]: d }));
    } catch {
      setDetailById((m) => ({ ...m, [id]: null }));
    } finally {
      setDetailLoading((m) => ({ ...m, [id]: false }));
    }
  }, [detailById]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-5">
      <h1 className="mb-4 text-2xl font-bold text-[var(--color-text)]">
        {t("title")}
      </h1>

      <div className="mb-4 flex gap-1 border-b border-[var(--color-border)]">
        <button
          type="button"
          onClick={() => setTab("team")}
          className={cn(
            "min-h-11 border-b-2 px-3 py-2 text-sm font-medium transition-colors",
            tab === "team"
              ? "border-[var(--color-primary)] text-[var(--color-text)]"
              : "border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text)]"
          )}
        >
          {t("tabTeam")}
        </button>
        <button
          type="button"
          onClick={() => setTab("people")}
          className={cn(
            "min-h-11 border-b-2 px-3 py-2 text-sm font-medium transition-colors",
            tab === "people"
              ? "border-[var(--color-primary)] text-[var(--color-text)]"
              : "border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text)]"
          )}
        >
          {t("tabPeople")}
        </button>
      </div>

      {tab === "team" && (
        <>
          {loadingComm && (
            <p className="text-sm text-[var(--color-text-secondary)]">
              {t("loading")}
            </p>
          )}
          {commErr && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-red-800">
              {commErr}
            </div>
          )}
          {community && !commErr && (
            <div className="space-y-5">
              <section>
                <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-[var(--color-text-secondary)]">
                  {t("teamOverview")}
                </h2>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                  <div className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 shadow-[var(--shadow-sm)]">
                    <p className="text-lg font-semibold tabular-nums text-[var(--color-text)]">
                      {community.total_events}
                    </p>
                    <p className="text-xs text-[var(--color-text-secondary)]">
                      {t("eventsPlural", { count: community.total_events })}
                    </p>
                  </div>
                  <div className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 shadow-[var(--shadow-sm)]">
                    <p className="text-lg font-semibold tabular-nums text-[var(--color-text)]">
                      {community.total_participants}
                    </p>
                    <p className="text-xs text-[var(--color-text-secondary)]">
                      {t("totalParticipants")}
                    </p>
                  </div>
                  <div className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 shadow-[var(--shadow-sm)]">
                    <p className="text-xs text-[var(--color-text-secondary)]">
                      {t("mostActive")}
                    </p>
                    <p className="truncate text-base font-semibold text-[var(--color-text)]">
                      {community.most_active_participant?.display_name ?? "—"}
                    </p>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="mb-2 text-sm font-semibold text-[var(--color-text)]">
                  {t("bySport")}
                </h3>
                {sportBars.length === 0 ? (
                  <p className="text-sm text-[var(--color-text-secondary)]">
                    {t("noData")}
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {sportBars.map((row) => (
                      <li
                        key={row.key}
                        className="flex items-center gap-2 text-sm sm:gap-3"
                      >
                        <div className="min-w-0 flex-1">
                          <div className="h-2.5 overflow-hidden rounded-full bg-[var(--color-surface-tinted)]">
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${(row.value / maxSportCount) * 100}%`,
                                backgroundColor: sportFill(row.key) as string,
                              }}
                            />
                          </div>
                        </div>
                        <span className="w-[5.5rem] shrink-0 font-medium text-[var(--color-text)] sm:w-28">
                          {row.name}
                        </span>
                        <span className="shrink-0 whitespace-nowrap text-xs text-[var(--color-text-secondary)] sm:text-sm">
                          {t("eventsPlural", { count: row.value })}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              <section>
                <h3 className="mb-2 text-sm font-semibold text-[var(--color-text)]">
                  {t("popularLocations")}
                </h3>
                {barData.length === 0 ? (
                  <p className="text-sm text-[var(--color-text-secondary)]">
                    {t("noData")}
                  </p>
                ) : (
                  <div
                    className="min-h-[200px] w-full min-w-0"
                    style={{ height: locationsChartHeight }}
                  >
                    <ResponsiveContainer
                      width="100%"
                      height={locationsChartHeight}
                    >
                      <BarChart
                        layout="vertical"
                        data={barData}
                        margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                        <XAxis type="number" allowDecimals={false} />
                        <YAxis
                          type="category"
                          dataKey="location"
                          width={88}
                          tick={{ fontSize: 11 }}
                        />
                        <Tooltip
                          formatter={(v) => [
                            t("eventsPlural", { count: Number(v ?? 0) }),
                            "",
                          ]}
                          labelFormatter={(_, payload) =>
                            (payload?.[0]?.payload as { full?: string })
                              ?.full ?? ""
                          }
                        />
                        <Bar dataKey="count" fill="#64748b" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </section>
            </div>
          )}
        </>
      )}

      {tab === "people" && (
        <>
          {loadingPeople && (
            <p className="text-sm text-[var(--color-text-secondary)]">
              {t("loading")}
            </p>
          )}
          {peopleErr && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-red-800">
              {peopleErr}
            </div>
          )}
          {!loadingPeople && !peopleErr && (
            <div className="grid gap-2 sm:grid-cols-2 sm:gap-3">
              {sortedParticipants.map((p) => {
                const st = statsById[p.id];
                const total = st?.total_events ?? 0;
                const bySport = st?.events_by_sport ?? {};
                const records = st?.personal_records ?? {};
                const places = st?.places_history ?? [];
                const isOpen = expanded[p.id];
                const detail = detailById[p.id];

                return (
                  <Card
                    key={p.id}
                    className="border-[var(--color-border)] bg-[var(--color-surface)] p-3 shadow-[var(--shadow-sm)]"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-[var(--color-text)]">
                          👤 {p.display_name}
                          {p.telegram_username ? (
                            <span className="font-normal text-[var(--color-text-secondary)]">
                              {" "}
                              (@{p.telegram_username})
                            </span>
                          ) : null}
                        </p>
                      </div>
                    </div>

                    {total === 0 ? (
                      <p className="mt-1.5 text-xs text-[var(--color-text-secondary)]">
                        {t("noEvents")}
                      </p>
                    ) : (
                      <>
                        <p className="mt-1.5 text-xs font-medium text-[var(--color-text)]">
                          🏁 {t("eventsPlural", { count: total })}
                        </p>
                        <p className="mt-1.5 flex flex-wrap gap-x-2 gap-y-1 text-[11px] text-[var(--color-text-secondary)]">
                          {Object.entries(bySport)
                            .sort((a, b) => b[1] - a[1])
                            .map(([k, n]) => (
                              <span key={k} className="inline-flex items-center gap-1">
                                <SportIcon
                                  sport={isSportType(k) ? k : "other"}
                                  className="shrink-0"
                                />
                                {sportLabelLocalized(k)}: {n}
                              </span>
                            ))}
                        </p>
                        {Object.keys(records).length > 0 && (
                          <div className="mt-2 text-xs">
                            <p className="flex items-center gap-1.5 font-medium text-[var(--color-text)]">
                              <SportIcon sport="other" size={14} />
                              {t("personalRecords")}
                            </p>
                            <ul className="mt-1 list-inside list-disc text-[var(--color-text-secondary)]">
                              {Object.entries(records).map(([dist, time]) => (
                                <li key={dist}>
                                  {dist} — {time}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {places.length > 0 && (
                          <div className="mt-2 text-xs">
                            <p className="font-medium text-[var(--color-text)]">
                              📍 {t("recentPlaces")}
                            </p>
                            <ul className="mt-1 space-y-0.5 text-[var(--color-text-secondary)]">
                              {places.slice(0, 3).map((pl, i) => (
                                <li key={i}>
                                  • {pl.event_name} — {pl.result_place}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </>
                    )}

                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="mt-2 w-full sm:mt-3 sm:w-auto"
                      onClick={() => void toggleDetail(p.id)}
                    >
                      {t("more")}
                    </Button>

                    {isOpen && (
                      <div className="mt-2 border-t border-[var(--color-border)] pt-2 text-xs">
                        {detailLoading[p.id] && (
                          <p className="text-[var(--color-text-muted)]">
                            {t("loading")}
                          </p>
                        )}
                        {!detailLoading[p.id] && detail === null && (
                          <p className="text-[var(--color-text-secondary)]">
                            {t("detailLoadFailed")}
                          </p>
                        )}
                        {!detailLoading[p.id] &&
                          detail &&
                          detail.events.length === 0 && (
                            <p className="text-[var(--color-text-secondary)]">
                              {t("noEventsInList")}
                            </p>
                          )}
                        {!detailLoading[p.id] && detail && detail.events.length > 0 && (
                          <ul className="max-h-52 space-y-1.5 overflow-y-auto">
                            {detail.events.map((ev) => (
                              <li
                                key={ev.registration_id}
                                className="rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface-tinted)] px-2 py-1"
                              >
                                <span className="font-medium text-[var(--color-text)]">
                                  {ev.event_name}
                                </span>
                                <span className="text-[var(--color-text-secondary)]">
                                  {" "}
                                  · {ev.date_start} · {ev.location}
                                </span>
                                <div className="text-[var(--color-text-muted)]">
                                  {(ev.distances || []).join(", ")}
                                  {ev.result_time ? ` · ⏱ ${ev.result_time}` : ""}
                                  {ev.result_place ? ` · ${ev.result_place}` : ""}
                                </div>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}
                  </Card>
                );
              })}
              {sortedParticipants.length === 0 && (
                <p className="col-span-full text-sm text-[var(--color-text-secondary)]">
                  {t("noParticipantsYet")}
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
