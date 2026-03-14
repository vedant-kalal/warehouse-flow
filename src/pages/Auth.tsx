import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { api } from '@/lib/api';

export default function Auth() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('login');
  const [loading, setLoading] = useState(false);
  const [forgotMode, setForgotMode] = useState<'idle' | 'email' | 'otp'>('idle');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [otpEmail, setOtpEmail] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    await api.login(email, password);
    setLoading(false);
    navigate('/dashboard');
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    await api.signup(email, password, name);
    setLoading(false);
    navigate('/dashboard');
  };

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    await api.requestOtp(otpEmail);
    setLoading(false);
    setForgotMode('otp');
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    await api.verifyOtp(otpEmail, otp.join(''));
    setLoading(false);
    setForgotMode('idle');
    setTab('login');
  };

  const handleOtpChange = (i: number, v: string) => {
    if (v.length > 1) return;
    const next = [...otp];
    next[i] = v;
    setOtp(next);
    if (v && i < 5) {
      const el = document.getElementById(`otp-${i + 1}`);
      el?.focus();
    }
  };

  if (forgotMode !== 'idle') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <div className="w-full max-w-[380px] bg-card border border-border rounded-xl p-6 surface-border animate-scale-in">
          <h1 className="text-lg font-semibold mb-1 text-foreground">Reset Password</h1>
          {forgotMode === 'email' ? (
            <form onSubmit={handleRequestOtp} className="space-y-4 mt-4">
              <p className="text-sm text-muted-foreground">Enter your email to receive a 6-digit OTP.</p>
              <div className="space-y-2">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Email</Label>
                <Input value={otpEmail} onChange={e => setOtpEmail(e.target.value)} type="email" required className="bg-surface border-border" />
              </div>
              <Button type="submit" className="w-full btn-press" disabled={loading}>{loading ? 'Sending...' : 'Send OTP'}</Button>
              <button type="button" onClick={() => setForgotMode('idle')} className="text-xs text-muted-foreground hover:text-foreground w-full text-center">Back to login</button>
            </form>
          ) : (
            <form onSubmit={handleVerifyOtp} className="space-y-4 mt-4">
              <p className="text-sm text-muted-foreground">Enter the 6-digit code sent to <span className="font-mono text-foreground">{otpEmail}</span></p>
              <div className="flex gap-2 justify-center">
                {otp.map((d, i) => (
                  <input
                    key={i}
                    id={`otp-${i}`}
                    value={d}
                    onChange={e => handleOtpChange(i, e.target.value)}
                    maxLength={1}
                    className="w-10 h-12 text-center text-2xl font-mono bg-surface border border-border rounded-sm text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                ))}
              </div>
              <Button type="submit" className="w-full btn-press" disabled={loading || otp.some(d => !d)}>{loading ? 'Verifying...' : 'Verify OTP'}</Button>
              <button type="button" onClick={() => setForgotMode('email')} className="text-xs text-muted-foreground hover:text-foreground w-full text-center">Resend code</button>
            </form>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-[380px] bg-card border border-border rounded-lg p-6 surface-border">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-8 h-8 bg-primary rounded-sm flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">CI</span>
          </div>
          <span className="font-semibold text-foreground">Access CoreInventory</span>
        </div>
        <Tabs value={tab} onValueChange={setTab} className="w-full">
          <TabsList className="w-full bg-muted rounded-sm">
            <TabsTrigger value="login" className="flex-1 rounded-sm text-xs uppercase tracking-wider data-[state=active]:bg-surface data-[state=active]:text-foreground">Login</TabsTrigger>
            <TabsTrigger value="signup" className="flex-1 rounded-sm text-xs uppercase tracking-wider data-[state=active]:bg-surface data-[state=active]:text-foreground">Sign Up</TabsTrigger>
          </TabsList>
          <TabsContent value="login">
            <form onSubmit={handleLogin} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Email</Label>
                <Input value={email} onChange={e => setEmail(e.target.value)} type="email" required className="bg-surface border-border" />
              </div>
              <div className="space-y-2">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Password</Label>
                <Input value={password} onChange={e => setPassword(e.target.value)} type="password" required className="bg-surface border-border" />
              </div>
              <Button type="submit" className="w-full btn-press" disabled={loading}>{loading ? 'Authenticating...' : 'Login'}</Button>
              <button type="button" onClick={() => { setForgotMode('email'); setOtpEmail(email); }} className="text-xs text-muted-foreground hover:text-foreground w-full text-center">Forgot password?</button>
            </form>
          </TabsContent>
          <TabsContent value="signup">
            <form onSubmit={handleSignup} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Full Name</Label>
                <Input value={name} onChange={e => setName(e.target.value)} required className="bg-surface border-border" />
              </div>
              <div className="space-y-2">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Email</Label>
                <Input value={email} onChange={e => setEmail(e.target.value)} type="email" required className="bg-surface border-border" />
              </div>
              <div className="space-y-2">
                <Label className="text-xs uppercase tracking-wider text-muted-foreground">Password</Label>
                <Input value={password} onChange={e => setPassword(e.target.value)} type="password" required className="bg-surface border-border" />
              </div>
              <Button type="submit" className="w-full btn-press" disabled={loading}>{loading ? 'Creating account...' : 'Sign Up'}</Button>
            </form>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
