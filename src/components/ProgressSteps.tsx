import { cn } from '@/lib/utils';
import type { Status } from '@/lib/types';

const steps: Status[] = ['draft', 'confirmed', 'done'];
const stepLabels: Record<string, string> = { draft: 'Draft', confirmed: 'Confirmed', done: 'Done' };

export function ProgressSteps({ current }: { current: Status }) {
  const currentIdx = steps.indexOf(current);

  return (
    <div className="flex items-center gap-0 w-full max-w-md">
      {steps.map((step, i) => {
        const isActive = i <= currentIdx;
        const isCurrent = i === currentIdx;
        return (
          <div key={step} className="flex items-center flex-1">
            <div className="flex flex-col items-center gap-1">
              <div className={cn(
                'w-3 h-3 rounded-full border-2 transition-snappy',
                isActive ? 'border-primary bg-primary' : 'border-muted-foreground/30 bg-transparent',
                isCurrent && 'ring-2 ring-primary/30'
              )} />
              <span className={cn('text-[10px] font-mono uppercase tracking-wider', isActive ? 'text-foreground' : 'text-muted-foreground')}>{stepLabels[step]}</span>
            </div>
            {i < steps.length - 1 && (
              <div className={cn('flex-1 h-px mx-2', i < currentIdx ? 'bg-primary' : 'bg-muted')} />
            )}
          </div>
        );
      })}
    </div>
  );
}
