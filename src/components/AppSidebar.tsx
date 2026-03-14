import {
  LayoutDashboard, Package, ArrowDownToLine, ArrowUpFromLine, ArrowLeftRight,
  History, ClipboardList, Building2, MapPin, User,
} from 'lucide-react';
import { NavLink } from '@/components/NavLink';
import { useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarFooter, useSidebar,
} from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';

const mainItems = [
  { title: 'Dashboard', url: '/dashboard', icon: LayoutDashboard },
  { title: 'Products', url: '/products', icon: Package, badgeKey: 'products' as const },
  { title: 'Receipts', url: '/receipts', icon: ArrowDownToLine, badgeKey: 'receipts' as const },
  { title: 'Deliveries', url: '/deliveries', icon: ArrowUpFromLine },
  { title: 'Transfers', url: '/transfers', icon: ArrowLeftRight },
  { title: 'Move History', url: '/moves', icon: History },
  { title: 'Adjustments', url: '/adjustments', icon: ClipboardList },
];

const configItems = [
  { title: 'Warehouses', url: '/warehouses', icon: Building2 },
  { title: 'Locations', url: '/locations', icon: MapPin },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === 'collapsed';
  const location = useLocation();
  const [badges, setBadges] = useState<{ products: number; receipts: number }>({ products: 0, receipts: 0 });

  useEffect(() => {
    Promise.all([api.getProducts(), api.getReceipts()]).then(([prods, recs]) => {
      const lowStock = prods.filter(p => p.onHand <= p.reorderPoint).length;
      const confirmedReceipts = recs.filter(r => r.status === 'confirmed').length;
      setBadges({ products: lowStock, receipts: confirmedReceipts });
    });
  }, [location.pathname]);

  const isActive = (path: string) => location.pathname === path || location.pathname.startsWith(path + '/');

  const renderItem = (item: typeof mainItems[0]) => {
    const badge = 'badgeKey' in item && item.badgeKey ? badges[item.badgeKey] : 0;
    return (
      <SidebarMenuItem key={item.title}>
        <SidebarMenuButton asChild>
          <NavLink
            to={item.url}
            end={item.url === '/dashboard'}
            className={cn('flex items-center gap-3 px-3 py-2 text-sm rounded-lg transition-all duration-200', isActive(item.url) ? 'bg-accent text-foreground' : 'text-sidebar-foreground hover:bg-accent/50')}
            activeClassName="bg-accent text-foreground"
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!collapsed && (
              <>
                <span className="flex-1">{item.title}</span>
                {badge > 0 && (
                  <span className={cn('text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-full bg-primary/20 text-primary', badge > 0 && 'animate-pulse-badge')}>
                    {badge}
                  </span>
                )}
              </>
            )}
          </NavLink>
        </SidebarMenuButton>
      </SidebarMenuItem>
    );
  };

  return (
    <Sidebar collapsible="icon" className="border-r border-border">
      <div className={cn('px-4 py-4 border-b border-border', collapsed && 'px-2')}>
        {collapsed ? (
          <span className="text-primary font-bold text-lg block text-center">C</span>
        ) : (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-primary rounded-sm flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-xs">CI</span>
            </div>
            <span className="font-semibold text-sm tracking-tight text-foreground">CoreInventory</span>
          </div>
        )}
      </div>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-widest text-muted-foreground px-3">Operations</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>{mainItems.map(renderItem)}</SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-widest text-muted-foreground px-3">Configuration</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>{configItems.map(renderItem)}</SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="border-t border-border p-2">
        <SidebarMenuItem>
          <SidebarMenuButton asChild>
            <NavLink to="/profile" className={cn('flex items-center gap-3 px-3 py-2 text-sm rounded-sm transition-snappy', isActive('/profile') ? 'bg-accent text-foreground' : 'text-sidebar-foreground hover:bg-accent/50')} activeClassName="bg-accent text-foreground">
              <User className="h-4 w-4 shrink-0" />
              {!collapsed && <span>Profile</span>}
            </NavLink>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarFooter>
    </Sidebar>
  );
}
