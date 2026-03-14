import { cn } from '@/lib/utils';

interface StockBarProps {
  onHand: number;
  reorderPoint: number;
  className?: string;
}

export function StockBar({ onHand, reorderPoint, className }: StockBarProps) {
  const ratio = reorderPoint > 0 ? onHand / reorderPoint : onHand > 0 ? 2 : 0;
  const pct = Math.min(ratio * 50, 100); // 100% at 2x reorder
  const color = onHand === 0 ? 'bg-stock-critical' : ratio <= 1 ? 'bg-stock-warning' : 'bg-stock-healthy';

  return (
    <div className={cn('w-16 h-1.5 rounded-sm overflow-hidden', className)} style={{ backgroundColor: 'hsl(0 0% 15%)' }}>
      <div className={cn('h-full rounded-sm transition-snappy', color)} style={{ width: `${pct}%` }} />
    </div>
  );
}
