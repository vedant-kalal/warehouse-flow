import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Warehouse } from '@/lib/types';
import { Layout } from '@/components/Layout';
import { Building2, MapPin } from 'lucide-react';

export default function Warehouses() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);

  useEffect(() => { api.getWarehouses().then(setWarehouses); }, []);

  return (
    <Layout>
      <div className="p-6 space-y-4 max-w-7xl">
        <h1 className="text-lg font-semibold">Warehouses</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {warehouses.map(w => (
            <div key={w.id} className="bg-card border border-border rounded-sm p-4 space-y-3 surface-glow">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-sm">{w.name}</h3>
                  <span className="font-mono text-xs text-muted-foreground">{w.code}</span>
                </div>
                <Building2 className="h-4 w-4 text-muted-foreground" />
              </div>
              <p className="text-xs text-muted-foreground">{w.address}</p>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <MapPin className="h-3 w-3" />
                <span className="font-mono">{w.locationCount}</span> locations
              </div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
