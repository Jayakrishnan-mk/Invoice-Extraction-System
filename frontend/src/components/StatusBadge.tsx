const COLORS: Record<string, string> = {
  completed: 'bg-emerald-100 text-emerald-800',
  paid: 'bg-emerald-100 text-emerald-800',
  failed: 'bg-red-100 text-red-800',
  unpaid: 'bg-amber-100 text-amber-800',
  unknown: 'bg-slate-200 text-slate-700',
};

export default function StatusBadge({ value }: { value: string }) {
  const colorClass = COLORS[value] ?? 'bg-slate-200 text-slate-700';
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${colorClass}`}>
      {value}
    </span>
  );
}
