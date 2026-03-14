import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Product, Receipt, Delivery, Transfer } from '@/lib/types';
import { Layout } from '@/components/Layout';
import { StatusBadge } from '@/components/StatusBadge';
import { TypeBadge } from '@/components/TypeBadge';
import { SearchBar } from '@/components/SearchBar';
import { cn } from '@/lib/utils';
import { AlertTriangle, Package, ArrowDownToLine, ArrowUpFromLine, ArrowLeftRight, Building2 } from 'lucide-react';

type FilterType = 'all' | 'receipt' | 'delivery' | 'transfer';
type FilterStatus = 'all' | 'draft' | 'confirmed' | 'done';

export default function Dashboard() {
  const [products, setProducts] = useState<Product[]>([]);
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<FilterType>('all');
  const [statusFilter, setStatusFilter] = useState<FilterStatus>('all');

  useEffect(() => {
    Promise.all([api.getProducts(), api.getReceipts(), api.getDeliveries(), api.getTransfers()]).then(([p, r, d, t]) => {
      setProducts(p); setReceipts(r); setDeliveries(d); setTransfers(t);
    });
  }, []);

  const totalOnHand = products.reduce((s, p) => s + p.onHand, 0);
  const lowStock = products.filter(p => p.onHand > 0 && p.onHand <= p.reorderPoint).length;
  const outOfStock = products.filter(p => p.onHand === 0).length;
  const pendingReceipts = receipts.filter(r => r.status !== 'done' && r.status !== 'cancelled').length;
  const pendingDeliveries = deliveries.filter(d => d.status !== 'done' && d.status !== 'cancelled').length;

  const kpis = [
    { label: 'Total On Hand', value: totalOnHand.toLocaleString(), icon: Package, alert: false },
    { label: 'Low / Out of Stock', value: `${lowStock + outOfStock}`, icon: AlertTriangle, alert: lowStock + outOfStock > 0 },
    { label: 'Pending Receipts', value: pendingReceipts.toString(), icon: ArrowDownToLine, alert: false },
    { label: 'Pending Deliveries', value: pendingDeliveries.toString(), icon: ArrowUpFromLine, alert: false },
    { label: 'Warehouses', value: '2', icon: Building2, alert: false },
  ];

  type OpRow = { type: 'receipt' | 'delivery' | 'transfer'; reference: string; partner: string; date: string; status: 'draft' | 'confirmed' | 'done' | 'cancelled'; lines: number };
  const operations: OpRow[] = [
    ...receipts.map(r => ({ type: 'receipt' as const, reference: r.reference, partner: r.supplier, date: r.scheduledDate, status: r.status, lines: r.lines.length })),
    ...deliveries.map(d => ({ type: 'delivery' as const, reference: d.reference, partner: d.customer, date: d.scheduledDate, status: d.status, lines: d.lines.length })),
    ...transfers.map(t => ({ type: 'transfer' as const, reference: t.reference, partner: `${t.fromLocation} → ${t.toLocation}`, date: t.scheduledDate, status: t.status, lines: t.lines.length })),
  ].filter(op => {
    if (typeFilter !== 'all' && op.type !== typeFilter) return false;
    if (statusFilter !== 'all' && op.status !== statusFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      return op.reference.toLowerCase().includes(q) || op.partner.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <Layout>
      <div className="p-6 space-y-6 max-w-7xl">
        <h1 className="text-lg font-semibold">Dashboard</h1>

        {outOfStock > 0 && (
          <div className="flex items-center gap-3 px-4 py-3 bg-primary/10 border border-primary/20 rounded-sm">
            <AlertTriangle className="h-4 w-4 text-primary shrink-0" />
            <span className="text-sm"><span className="font-mono font-semibold text-primary">{outOfStock}</span> product(s) out of stock. Review inventory immediately.</span>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-5 gap-4">
          {kpis.map((kpi, idx) => (
            <div key={kpi.label} className={cn('h-24 bg-card border rounded-lg p-4 flex flex-col justify-between surface-glow animate-fade-in hover:scale-[1.02] transition-transform duration-200', kpi.alert ? 'border-primary' : 'border-border')} style={{ animationDelay: `${idx * 80}ms`, animationFillMode: 'both' }}>
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground">{kpi.label}</span>
                <kpi.icon className={cn('h-3.5 w-3.5', kpi.alert ? 'text-primary' : 'text-muted-foreground')} />
              </div>
              <span className={cn('text-2xl font-mono font-semibold', kpi.alert ? 'text-primary' : 'text-foreground')}>{kpi.value}</span>
            </div>
          ))}
        </div>

        {/* Operations Table */}
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <SearchBar value={search} onChange={setSearch} placeholder="Search reference or partner..." />
            <div className="flex gap-1">
              {(['all', 'receipt', 'delivery', 'transfer'] as FilterType[]).map(t => (
                <button key={t} onClick={() => setTypeFilter(t)} className={cn('px-3 py-1.5 text-xs rounded-full font-mono uppercase tracking-wider transition-all duration-200 btn-press', typeFilter === t ? 'bg-accent text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-accent/50')}>
                  {t === 'all' ? 'All' : t}
                </button>
              ))}
            </div>
            <div className="flex gap-1">
              {(['all', 'draft', 'confirmed', 'done'] as FilterStatus[]).map(s => (
                <button key={s} onClick={() => setStatusFilter(s)} className={cn('px-3 py-1.5 text-xs rounded-full font-mono uppercase tracking-wider transition-all duration-200 btn-press', statusFilter === s ? 'bg-accent text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-accent/50')}>
                  {s === 'all' ? 'All' : s}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg overflow-hidden animate-fade-in" style={{ animationDelay: '300ms', animationFillMode: 'both' }}>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 px-3 text-[10px] uppercase tracking-widest text-muted-foreground font-medium">Type</th>
                  <th className="text-left py-2 px-3 text-[10px] uppercase tracking-widest text-muted-foreground font-medium">Reference</th>
                  <th className="text-left py-2 px-3 text-[10px] uppercase tracking-widest text-muted-foreground font-medium">Partner / Route</th>
                  <th className="text-left py-2 px-3 text-[10px] uppercase tracking-widest text-muted-foreground font-medium">Date</th>
                  <th className="text-left py-2 px-3 text-[10px] uppercase tracking-widest text-muted-foreground font-medium">Lines</th>
                  <th className="text-left py-2 px-3 text-[10px] uppercase tracking-widest text-muted-foreground font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {operations.map((op, i) => (
                  <tr key={i} className="border-b border-border last:border-0 row-hover">
                    <td className="py-2 px-3"><TypeBadge type={op.type} /></td>
                    <td className="py-2 px-3 font-mono text-xs">{op.reference}</td>
                    <td className="py-2 px-3 text-sm">{op.partner}</td>
                    <td className="py-2 px-3 font-mono text-xs text-muted-foreground">{op.date}</td>
                    <td className="py-2 px-3 font-mono text-xs">{op.lines}</td>
                    <td className="py-2 px-3"><StatusBadge status={op.status} /></td>
                  </tr>
                ))}
                {operations.length === 0 && (
                  <tr><td colSpan={6} className="py-8 text-center text-muted-foreground text-sm font-mono">No records found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  );
}
