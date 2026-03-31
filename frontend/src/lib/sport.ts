import type { SportType } from "./types";

export const SPORT_DOT: Record<SportType, string> = {
  swimming: "var(--sport-swimming)",
  running: "var(--sport-running)",
  cycling: "var(--sport-cycling)",
  triathlon: "var(--sport-triathlon)",
  other: "var(--sport-other)",
};

export const SPORT_LABEL: Record<SportType, string> = {
  swimming: "Плавание",
  running: "Бег",
  cycling: "Велогонка",
  triathlon: "Триатлон",
  other: "Прочее",
};

export const SPORT_BORDER: Record<SportType, string> = {
  swimming: "border-l-[var(--sport-swimming)]",
  running: "border-l-[var(--sport-running)]",
  cycling: "border-l-[var(--sport-cycling)]",
  triathlon: "border-l-[var(--sport-triathlon)]",
  other: "border-l-[var(--sport-other)]",
};

/** Фон и текст для блока даты на компактной карточке */
export const SPORT_CARD_DATE: Record<
  SportType,
  { bg: string; text: string }
> = {
  swimming: {
    bg: "var(--sport-swimming-bg)",
    text: "var(--sport-swimming-text)",
  },
  running: {
    bg: "var(--sport-running-bg)",
    text: "var(--sport-running-text)",
  },
  cycling: {
    bg: "var(--sport-cycling-bg)",
    text: "var(--sport-cycling-text)",
  },
  triathlon: {
    bg: "var(--sport-triathlon-bg)",
    text: "var(--sport-triathlon-text)",
  },
  other: {
    bg: "var(--sport-other-bg)",
    text: "var(--sport-other-text)",
  },
};
