"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Props = {
  title: string;
  description?: string;
  className?: string;
  actionHref?: string;
  actionLabel?: string;
  onAction?: () => void;
  actionButtonLabel?: string;
};

export function EmptyStateCard({
  title,
  description,
  className,
  actionHref,
  actionLabel,
  onAction,
  actionButtonLabel,
}: Props) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-[var(--radius-lg)] border border-dashed border-[var(--color-border)] bg-[var(--color-surface-tinted)] px-6 py-12 text-center",
        className
      )}
    >
      <h3 className="text-lg font-medium text-[var(--color-text)]">{title}</h3>
      {description ? (
        <p className="mt-2 max-w-md text-sm text-[var(--color-text-muted)]">
          {description}
        </p>
      ) : null}
      {actionHref && actionLabel ? (
        <Link
          href={actionHref}
          className="btn-accent mt-6 inline-flex min-h-11 items-center justify-center rounded-[var(--radius-full)] px-5 text-sm font-medium text-[var(--color-accent-text)] no-underline"
        >
          {actionLabel}
        </Link>
      ) : null}
      {onAction && actionButtonLabel ? (
        <Button
          type="button"
          className="mt-6 bg-[var(--color-accent)] text-[var(--color-accent-text)] hover:bg-[var(--color-accent-hover)]"
          onClick={onAction}
        >
          {actionButtonLabel}
        </Button>
      ) : null}
    </div>
  );
}

type ServerProps = {
  title: string;
  description: string;
  retryLabel: string;
  onRetry: () => void;
  className?: string;
};

export function ServerUnavailableCard({
  title,
  description,
  retryLabel,
  onRetry,
  className,
}: ServerProps) {
  return (
    <div
      role="alert"
      className={cn(
        "rounded-[var(--radius-lg)] border-2 border-amber-400 bg-amber-50/95 px-6 py-5 text-[var(--color-text)] shadow-sm dark:border-amber-500/70 dark:bg-amber-950/35 dark:text-amber-50",
        className
      )}
    >
      <p className="font-medium">⚠️ {title}</p>
      <p className="mt-1 text-sm text-[var(--color-text-secondary)] dark:text-amber-100/85">
        {description}
      </p>
      <Button
        type="button"
        variant="outline"
        className="mt-4 border-amber-600 text-[var(--color-text)] hover:bg-amber-100 dark:border-amber-400 dark:hover:bg-amber-900/40"
        onClick={onRetry}
      >
        {retryLabel}
      </Button>
    </div>
  );
}
