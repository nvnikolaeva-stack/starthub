/**
 * Стандартные пресеты дистанций (как в API). Без «Other» — своя дистанция задаётся отдельно в UI.
 */
export const DISTANCE_PRESETS = {
  triathlon: [
    "Sprint",
    "Olympic",
    "Half Ironman (70.3)",
    "Ironman (140.6)",
  ],
  running: [
    "5K",
    "10K",
    "Half Marathon",
    "Marathon",
    "Ultra",
    "Fun Run",
    "Backyard",
    "Beer Mile",
  ],
  swimming: [] as const,
  cycling: [] as const,
  other: [] as const,
} as const;
