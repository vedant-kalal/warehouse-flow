import { cn } from '@/lib/utils';
import type { Status } from '@/lib/types';

const statusConfig: Record<Status, { label: string; className: string }> = {
  draft: { label: 'Draft', className: 'bg-status-draft/20 text-status-draft border-status-draft/30' },
  confirmed: { label: 'Confirmed', className: 'bg-status-confirmed/20 text-status-confirmed border-status-confirmed/30' },
  done: { label: 'Done', className: 'bg-status-done/20 text-status-done border-status-done/30' },
  cancelled: { label: 'Cancelled', className: 'bg-status-cancelled/20 text-status-cancelled border-status-cancelled/30' },
};

export function StatusBadge({ status, className }: { status: Status; className?: string }) {
  const config = statusConfig[status];
  return (
    <span className={cn('inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium font-mono uppercase tracking-wider transition-snappy', config.className, className)}>
      {config.label}
    </span>
  );
}
