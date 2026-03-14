import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import type { UserProfile } from '@/lib/types';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { LogOut, KeyRound } from 'lucide-react';

export default function Profile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const navigate = useNavigate();

  useEffect(() => { api.getProfile().then(setProfile); }, []);

  if (!profile) return <Layout><div className="p-6 text-muted-foreground font-mono">Loading...</div></Layout>;

  return (
    <Layout>
      <div className="p-6 space-y-6 max-w-lg">
        <h1 className="text-lg font-semibold">Profile</h1>
        <div className="bg-card border border-border rounded-sm p-6 space-y-6 surface-glow">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-primary rounded-sm flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-lg font-mono">{profile.avatar}</span>
            </div>
            <div>
              <h2 className="font-semibold">{profile.name}</h2>
              <p className="text-sm text-muted-foreground">{profile.role}</p>
            </div>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Email</span>
              <span className="font-mono text-xs">{profile.email}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Last Login</span>
              <span className="font-mono text-xs">{new Date(profile.lastLogin).toLocaleString()}</span>
            </div>
          </div>
          <div className="space-y-2">
            <Button variant="outline" className="w-full btn-press gap-2">
              <KeyRound className="h-4 w-4" /> Change Password via OTP
            </Button>
            <Button variant="outline" className="w-full btn-press gap-2 border-destructive text-destructive hover:bg-destructive/10" onClick={() => navigate('/')}>
              <LogOut className="h-4 w-4" /> Sign Out
            </Button>
          </div>
        </div>
      </div>
    </Layout>
  );
}
