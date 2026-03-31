"use client";

import { listParticipants } from "@/lib/api";
import type { Participant } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";

export type FriendEntry = {
  key: string;
  source: "api" | "manual";
  participantId?: string;
  displayName: string;
  telegramUsername: string | null;
  distance: string;
};

type Props = {
  selectedDistances: string[];
  authorName: string;
  onAuthorNameChange: (v: string) => void;
  authorDistance: string;
  onAuthorDistanceChange: (v: string) => void;
  friends: FriendEntry[];
  onFriendsChange: (friends: FriendEntry[]) => void;
  authorError?: boolean;
};

export function ParticipantSelector({
  selectedDistances,
  authorName,
  onAuthorNameChange,
  authorDistance,
  onAuthorDistanceChange,
  friends,
  onFriendsChange,
  authorError,
}: Props) {
  const tp = useTranslations("participants");
  const [apiList, setApiList] = useState<Participant[]>([]);
  const [manualDraft, setManualDraft] = useState("");
  const [apiSelect, setApiSelect] = useState("");
  const [dupMsg, setDupMsg] = useState<string | null>(null);
  const dupTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const manualRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    void listParticipants()
      .then(setApiList)
      .catch(() => setApiList([]));
  }, []);

  useEffect(
    () => () => {
      if (dupTimer.current) clearTimeout(dupTimer.current);
    },
    []
  );

  function flashDup(msg: string) {
    setDupMsg(msg);
    if (dupTimer.current) clearTimeout(dupTimer.current);
    dupTimer.current = setTimeout(() => {
      setDupMsg(null);
      dupTimer.current = null;
    }, 3500);
  }

  function firstDist() {
    return selectedDistances[0] ?? "";
  }

  function addFromApi(pid: string) {
    if (!pid) return;
    const p = apiList.find((x) => x.id === pid);
    if (!p) return;
    if (friends.some((f) => f.participantId === pid)) {
      flashDup(tp("duplicate"));
      setApiSelect("");
      return;
    }
    const dist =
      selectedDistances.length >= 1 ? selectedDistances[0] : "";
    onFriendsChange([
      ...friends,
      {
        key: `f-${Date.now()}-${Math.random()}`,
        source: "api",
        participantId: pid,
        displayName: p.display_name,
        telegramUsername: p.telegram_username ?? null,
        distance: dist,
      },
    ]);
    setApiSelect("");
  }

  function addManual() {
    const n = manualDraft.trim();
    if (!n) return;
    const low = n.toLowerCase();
    if (authorName.trim().toLowerCase() === low) {
      flashDup(tp("duplicate"));
      return;
    }
    if (
      friends.some((f) => f.displayName.trim().toLowerCase() === low)
    ) {
      flashDup(tp("duplicate"));
      return;
    }
    if (
      friends.some(
        (f) =>
          f.source === "api" &&
          f.displayName.trim().toLowerCase() === low
      )
    ) {
      flashDup(tp("duplicate"));
      return;
    }
    onFriendsChange([
      ...friends,
      {
        key: `f-${Date.now()}-${Math.random()}`,
        source: "manual",
        displayName: n,
        telegramUsername: null,
        distance: firstDist(),
      },
    ]);
    setManualDraft("");
  }

  function updateFriendDistance(key: string, d: string) {
    onFriendsChange(
      friends.map((f) => (f.key === key ? { ...f, distance: d } : f))
    );
  }

  function removeFriend(key: string) {
    onFriendsChange(friends.filter((f) => f.key !== key));
  }

  const onlyAuthor = friends.length === 0;
  const canPickDistance = selectedDistances.length > 0;

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50/80 p-4">
      <Label className="text-base font-semibold text-slate-900">
        {tp("sectionTitle")}
      </Label>
      <p className="mt-2 text-sm text-slate-700">
        {tp("autoRegistered")}
      </p>
      <p className="mt-1 text-sm text-slate-600">
        {tp("addFriends")}
      </p>

      <div className="mb-3 mt-3">
        <Label htmlFor="author-name" className="text-xs text-slate-600">
          {tp("yourNameLabel")}
        </Label>
        <Input
          id="author-name"
          value={authorName}
          onChange={(e) => onAuthorNameChange(e.target.value)}
          placeholder={tp("yourNamePlaceholder")}
          className={cn("mt-1", authorError && "border-red-500")}
        />
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <div className="min-w-[200px] flex-1">
          <select
            value={apiSelect}
            onChange={(e) => {
              const v = e.target.value;
              if (v) addFromApi(v);
            }}
            className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm"
          >
            <option value="">{tp("pickFromList")}</option>
            {apiList.map((p) => (
              <option key={p.id} value={p.id}>
                {p.display_name}
                {p.telegram_username ? ` (@${p.telegram_username})` : ""}
              </option>
            ))}
          </select>
        </div>
        <span className="hidden self-center text-sm text-slate-500 sm:block">
          {tp("or")}
        </span>
        <span className="text-center text-sm text-slate-500 sm:hidden">
          {tp("or")}
        </span>
        <div className="flex min-w-0 flex-1 gap-2">
          <Input
            id="participant-manual-name"
            ref={manualRef}
            value={manualDraft}
            onChange={(e) => setManualDraft(e.target.value)}
            placeholder={tp("manualPlaceholder")}
            className="min-w-0 flex-1"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addManual();
              }
            }}
          />
          <Button type="button" variant="outline" onClick={addManual}>
            {tp("add")}
          </Button>
        </div>
      </div>

      {dupMsg && (
        <p className="mt-2 text-sm text-amber-800">{dupMsg}</p>
      )}

      <p className="mt-4 text-sm font-medium text-slate-800">
        {tp("goingToEvent")}
      </p>
      <div className="mt-2 rounded-lg border-2 border-slate-200 bg-white p-3">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 pb-3">
            <span className="text-lg" aria-hidden>
              👤
            </span>
            <span className="font-medium text-slate-900">
              {authorName.trim() || tp("authorFallback")}
              {!authorName.trim() && (
                <span className="font-normal text-slate-500">
                  {tp("nameHint")}
                </span>
              )}
            </span>
            {authorName.trim() && canPickDistance && selectedDistances.length > 1 ? (
              <select
                value={
                  selectedDistances.includes(authorDistance)
                    ? authorDistance
                    : selectedDistances[0]
                }
                onChange={(e) => onAuthorDistanceChange(e.target.value)}
                className="ml-auto max-w-[10rem] rounded border border-slate-300 bg-white px-2 py-1 text-xs"
              >
                {selectedDistances.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            ) : authorName.trim() && canPickDistance && selectedDistances.length === 1 ? (
              <span className="ml-auto text-xs text-slate-600">
                {selectedDistances[0]}
              </span>
            ) : null}
          </div>

          {friends.map((f) => (
            <div
              key={f.key}
              className="flex flex-wrap items-center gap-2 border-b border-slate-50 pb-2 last:border-0 last:pb-0"
            >
              <span className="text-lg" aria-hidden>
                👤
              </span>
              <span className="min-w-0 flex-1 font-medium text-slate-900">
                {f.displayName}
                {f.telegramUsername ? (
                  <span className="font-normal text-slate-600">
                    {" "}
                    (@{f.telegramUsername})
                  </span>
                ) : null}
              </span>
              {canPickDistance && (
                <>
                  <span className="text-slate-400">—</span>
                  {selectedDistances.length > 1 ? (
                    <select
                      value={
                        selectedDistances.includes(f.distance)
                          ? f.distance
                          : selectedDistances[0]
                      }
                      onChange={(e) =>
                        updateFriendDistance(f.key, e.target.value)
                      }
                      className="max-w-[10rem] rounded border border-slate-300 bg-white px-2 py-1 text-xs"
                    >
                      {selectedDistances.map((d) => (
                        <option key={d} value={d}>
                          {d}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span className="text-xs text-slate-600">
                      {selectedDistances[0]}
                    </span>
                  )}
                </>
              )}
              <button
                type="button"
                className="ml-auto rounded p-1 text-lg leading-none text-red-600 hover:bg-red-50"
                aria-label={tp("removeAria", { name: f.displayName })}
                onClick={() => removeFriend(f.key)}
              >
                ✕
              </button>
            </div>
          ))}

          {onlyAuthor && (
            <p className="text-sm text-slate-500">{tp("onlyYou")}</p>
          )}

          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="w-full text-slate-700"
            onClick={() => manualRef.current?.focus()}
          >
            {tp("addMore")}
          </Button>
        </div>
      </div>
    </div>
  );
}
