import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Search, Activity, AlertCircle, Radar, PieChart,
  Terminal, Calendar, TrendingUp, ShieldCheck, Settings,
  LogOut, Bell, Menu, X, BookOpen, Shield, Globe, Lock
} from 'lucide-react';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import AgentPanel from './components/AgentPanel';
import RiskCard from './components/RiskCard';
import RadarView from './components/RadarView';
import MutualFundView from './components/MutualFundView';
import SIPPlannerView from './components/SIPPlannerView';
import MarketExplorerView from './components/MarketExplorerView';
import TerminalView from './components/TerminalView';
import PortfolioView from './components/PortfolioView';
import TradingViewChart from './components/TradingViewChart';
import TradeJournalView from './components/TradeJournalView';
import './index.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const AUTH_API_URL = import.meta.env.VITE_AUTH_API_URL || 'http://localhost:8001';
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || 'YOUR_GOOGLE_CLIENT_ID_HERE';

function App() {
  const [activeTab, setActiveTab] = useState('discover'); // discover, portfolio, terminal, sip, radar
  const [symbol, setSymbol] = useState('AAPL');
  const [assetType, setAssetType] = useState('stock');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('trading_brain_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [showSettings, setShowSettings] = useState(false);
  const [showSearchSuggestions, setShowSearchSuggestions] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  // ─── Notification Bell State ───────────────────────────────────────────────
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [notifUnread, setNotifUnread] = useState(0);
  const notifRef = useRef(null);

  // Fetch high-confidence signals and build notifications
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/radar/signals`);
        const json = await res.json();
        const signals = (json.signals || json.data || []).filter(
          s => (s.decision === 'BUY' || s.decision === 'SELL') && s.confidence >= 0.65
        );
        const items = signals.map(s => ({
          id: `${s.symbol}-${s.decision}`,
          symbol: s.symbol,
          decision: s.decision,
          confidence: s.confidence,
          price: s.entry_price ?? s.current_price,
          sl: s.stop_loss,
          tp: s.take_profit,
          target_status: s.target_status,
          target_label: s.target_label,
          ts: new Date(),
        }));
        setNotifications(items);
        setNotifUnread(prev => (items.length > (notifications.length || 0) ? items.length : prev));
      } catch { }
    };
    fetchNotifications();
    const id = setInterval(fetchNotifications, 30000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Close notification panel when clicking outside
  useEffect(() => {
    const handler = (e) => { if (notifRef.current && !notifRef.current.contains(e.target)) setShowNotifications(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Mock static suggestions vastly expanded
  const searchSuggestions = [
    { type: 'stock', symbol: 'NIFTY', name: 'Nifty 50 Index', label: 'India' },
    { type: 'stock', symbol: 'SENSEX', name: 'BSE Sensex Index', label: 'India' },
    { type: 'stock', symbol: 'BANKNIFTY', name: 'Nifty Bank Index', label: 'India' },
    { type: 'stock', symbol: 'BANKEX', name: 'BSE Bankex Index', label: 'India' },
    { type: 'stock', symbol: 'FINNIFTY', name: 'Nifty Fin Service', label: 'India' },
    { type: 'stock', symbol: 'RELIANCE.NS', name: 'Reliance Industries', label: 'Bluechip' },
    { type: 'stock', symbol: 'HDFCBANK.NS', name: 'HDFC Bank Ltd', label: 'Bluechip' },
    { type: 'stock', symbol: 'TATASTEEL.NS', name: 'Tata Steel Ltd', label: 'Bluechip' },
    { type: 'stock', symbol: 'GOLDBEES.NS', name: 'Nippon India Gold ETF', label: 'ETF' },
    { type: 'stock', symbol: 'LIQUIDBEES.NS', name: 'Nippon Liquid ETF', label: 'ETF' },
    { type: 'stock', symbol: 'GOLD', name: 'Gold Spot/Futures', label: 'Commodity' },
    { type: 'stock', symbol: 'SILVER', name: 'Silver Spot/Futures', label: 'Commodity' },
    { type: 'stock', symbol: 'AAPL', name: 'Apple Inc.', label: 'US Tech' },
    { type: 'stock', symbol: 'NVDA', name: 'NVIDIA Corp.', label: 'US Tech' },
    { type: 'stock', symbol: 'TSLA', name: 'Tesla, Inc.', label: 'US Tech' },
    { type: 'stock', symbol: 'BTC', name: 'Bitcoin', label: 'Crypto' },
    { type: 'stock', symbol: 'ETH', name: 'Ethereum', label: 'Crypto' },
    { type: 'mutualfund', symbol: 'VTSAX', name: 'Vanguard Total Stock', label: 'Fund' }
  ];

  const fetchData = async (e, specificType = assetType, specificSymbol = symbol) => {
    if (e) e.preventDefault();
    if (!specificSymbol) return;

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const endpoint = `${API_BASE_URL}/analyze/${specificType}/${specificSymbol.toUpperCase()}`;
      const response = await axios.get(endpoint);
      setData(response.data);
      setActiveTab('discover'); // Switch to discover to see results
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'An error occurred fetching data');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const res = await axios.post(`${AUTH_API_URL}/auth/google`, null, {
        params: { token: credentialResponse.credential }
      });
      const userData = {
        name: res.data.user.name,
        email: res.data.user.email,
        picture: res.data.user.picture,
        token: res.data.access_token
      };
      setUser(userData);
      localStorage.setItem('trading_brain_user', JSON.stringify(userData));
    } catch (err) {
      setError('Google Authentication Failed. Please try again.');
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('trading_brain_user');
  };

  const SidebarItem = ({ id, icon: Icon, label }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group ${activeTab === id
        ? 'bg-primary/10 text-primary border-r-4 border-primary'
        : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
        }`}
    >
      <Icon size={20} className={activeTab === id ? 'text-primary' : 'group-hover:text-white'} />
      <span className="text-sm font-semibold">{label}</span>
      {id === 'radar' && <div className="ml-auto size-2 rounded-full bg-emerald-accent animate-pulse"></div>}
    </button>
  );

  const LoginScreen = () => (
    <div className="fixed inset-0 bg-[#06090f] z-[100] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(19,109,236,0.1),transparent)] pointer-events-none"></div>
      <div className="w-full max-w-md bg-[#0d131c] border border-slate-800 rounded-3xl p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary/0 via-primary to-primary/0"></div>

        <div className="flex flex-col items-center mb-10">
          <div className="size-16 rounded-2xl bg-primary flex items-center justify-center text-white shadow-2xl shadow-primary/40 mb-6">
            <Activity size={32} strokeWidth={3} />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tighter mb-2 text-center">TRADING BRAIN</h1>
          <p className="text-slate-500 font-bold text-center text-sm uppercase tracking-widest gap-2 flex items-center">
            <Shield size={12} className="text-primary" /> Enterprise AI Access
          </p>
        </div>

        <div className="space-y-6">
          <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl text-center">
            <h3 className="text-white font-bold mb-4 flex items-center justify-center gap-2"><Globe size={16} className="text-primary" /> Public Access Mode (Training)</h3>
            <p className="text-slate-400 text-xs leading-relaxed mb-6">
              The system is currently in its initial high-accuracy training phase. Access is open to all testers to help refine the neural engines.
            </p>
            <div className="relative flex justify-center py-2">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={() => setError('Google Login Failed')}
                theme="filled_blue"
                shape="pill"
                size="large"
                width="100%"
              />
            </div>
          </div>

          <p className="text-[10px] text-slate-600 text-center font-bold uppercase tracking-widest flex items-center justify-center gap-2">
            <Lock size={10} /> Core Workflows Encrypted By SecureCoreGuard
          </p>
        </div>
      </div>
    </div>
  );

  if (!user) {
    return (
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
        <LoginScreen />
        {error && (
          <div className="fixed bottom-8 left-1/2 -translate-x-1/2 px-6 py-3 bg-rose-500/10 border border-rose-500/20 text-rose-500 rounded-xl text-sm font-bold shadow-2xl backdrop-blur-md">
            {error}
          </div>
        )}
      </GoogleOAuthProvider>
    );
  }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="flex h-screen bg-background-dark text-slate-100 font-display overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 flex-shrink-0 border-r border-slate-800 bg-[#0d131c] flex flex-col h-full shadow-2xl z-30">
          <div className="p-6">
            <div className="flex items-center gap-3 mb-10">
              <div className="size-10 rounded-xl bg-primary flex items-center justify-center text-white shadow-lg shadow-primary/30">
                <Activity size={24} strokeWidth={3} />
              </div>
              <div>
                <h1 className="text-white text-lg font-black leading-tight tracking-tight">TRADING BRAIN</h1>
                <p className="text-primary text-[10px] font-bold uppercase tracking-widest">Enterprise AI</p>
              </div>
            </div>

            <nav className="space-y-2">
              <SidebarItem id="discover" icon={TrendingUp} label="Discover" />
              <SidebarItem id="portfolio" icon={PieChart} label="Portfolio" />
              <SidebarItem id="terminal" icon={Terminal} label="Market Terminal" />
              <SidebarItem id="sip" icon={Calendar} label="SIP Planner" />
              <SidebarItem id="radar" icon={Radar} label="Live Radar" />
              <SidebarItem id="journal" icon={BookOpen} label="Trade Journal" />
            </nav>
          </div>

          <div className="mt-auto p-6 space-y-4">
            <div className="bg-slate-800/40 rounded-xl p-4 border border-slate-700/50 cursor-pointer hover:border-slate-500 transition-colors" onClick={() => setShowSettings(true)}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold text-slate-500 uppercase">System Status</span>
                <div className="size-2 rounded-full bg-emerald-accent shadow-[0_0_8px_rgba(16,185,129,0.4)]"></div>
              </div>
              <p className="text-xs font-semibold text-white">Institutional Mode (Active)</p>
              <p className="text-[10px] text-slate-500 mt-1">4 Agents Online · All Systems Nomimal</p>
            </div>
            <button className="w-full flex items-center gap-3 px-4 py-2.5 text-slate-500 hover:text-rose-400 transition-colors" onClick={() => setShowSettings(true)}>
              <Settings size={18} />
              <span className="text-sm font-bold">Preferences</span>
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-background-dark">
          {/* Header */}
          <header className="h-20 flex-shrink-0 border-b border-slate-800 bg-background-dark/50 backdrop-blur-xl flex items-center justify-between px-8 z-20">
            <div className="flex-1 max-w-2xl relative group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" size={18} />
              <form onSubmit={fetchData} className="w-full flex gap-2">
                <select
                  className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs font-bold text-slate-300 outline-none focus:ring-2 focus:ring-primary/50"
                  value={assetType}
                  onChange={(e) => setAssetType(e.target.value)}
                >
                  <option value="stock">STOCKS</option>
                  <option value="crypto">CRYPTO</option>
                  <option value="mutualfund">M-FUNDS</option>
                </select>
                <input
                  type="text"
                  value={symbol}
                  onChange={(e) => {
                    setSymbol(e.target.value);
                    setShowSearchSuggestions(e.target.value.length > 0);
                  }}
                  onFocus={() => { setSearchFocused(true); setShowSearchSuggestions(symbol.length > 0); }}
                  onBlur={() => setTimeout(() => { setSearchFocused(false); setShowSearchSuggestions(false); }, 200)}
                  placeholder="Search ANY Global/Indian Ticker (e.g. SENSEX, GOLDBEES.NS, AAPL)"
                  className="flex-1 bg-slate-900 border border-slate-800 rounded-xl pl-12 pr-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary/50 text-white placeholder:text-slate-600 shadow-inner w-full"
                />
              </form>

              {/* Adaptive Search Suggestions */}
              {(showSearchSuggestions || searchFocused) && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-[#0f172a] border border-slate-800 rounded-xl shadow-2xl z-50 overflow-hidden">
                  <div className="p-2 border-b border-slate-800 bg-slate-900/50">
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2">Trending Searches</p>
                  </div>
                  <ul>
                    {searchSuggestions.filter(s => s.symbol.toLowerCase().includes(symbol.toLowerCase()) || s.name.toLowerCase().includes(symbol.toLowerCase())).length > 0
                      ? searchSuggestions.filter(s => s.symbol.toLowerCase().includes(symbol.toLowerCase()) || s.name.toLowerCase().includes(symbol.toLowerCase())).map((item, idx) => (
                        <li
                          key={idx}
                          className="px-4 py-3 hover:bg-slate-800 cursor-pointer flex items-center justify-between text-sm group"
                          onMouseDown={() => {
                            setSymbol(item.symbol);
                            setAssetType(item.type);
                            fetchData(null, item.type, item.symbol);
                            setShowSearchSuggestions(false);
                          }}
                        >
                          <div className="flex items-center gap-3">
                            <span className="font-black text-white">{item.symbol}</span>
                            <span className="text-slate-500 text-xs">{item.name}</span>
                          </div>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-primary/20 text-primary font-bold uppercase">{item.label}</span>
                        </li>
                      ))
                      : <li className="px-4 py-4 text-xs text-slate-500 text-center flex flex-col items-center">
                        <span className="font-bold mb-1 block">Tip: Type any symbol directly!</span>
                        <span>(e.g., TATASTEEL.NS, ^NSEBANK, TSLA) and press Enter.</span>
                      </li>}
                  </ul>
                </div>
              )}
            </div>

            <div className="flex items-center gap-6">
              {/* ─── Notification Bell ─────────────────────────────────────── */}
              <div className="relative" ref={notifRef}>
                <button
                  onClick={() => { setShowNotifications(v => !v); setNotifUnread(0); }}
                  className="relative p-2 text-slate-400 hover:text-white transition-colors"
                  title="Notifications"
                >
                  <Bell size={20} />
                  {notifications.length > 0 && (
                    <div className="absolute top-1 right-1 min-w-[14px] h-[14px] bg-primary rounded-full border-2 border-[#0f172a] flex items-center justify-center">
                      {notifUnread > 0 && <span className="text-[7px] font-black text-black leading-none">{notifUnread > 9 ? '9+' : notifUnread}</span>}
                    </div>
                  )}
                </button>

                {/* Notification panel */}
                {showNotifications && (
                  <div className="absolute right-0 top-12 w-96 bg-[#0f1729] border border-slate-700 rounded-2xl shadow-2xl shadow-black/60 z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                    {/* Header */}
                    <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
                      <div className="flex items-center gap-2">
                        <Bell size={13} className="text-primary" />
                        <span className="text-xs font-black text-white uppercase tracking-wider">AI Signal Alerts</span>
                        <span className="text-[9px] bg-primary/20 text-primary px-1.5 py-0.5 rounded font-black border border-primary/30">{notifications.length}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[9px] text-slate-600 font-mono">Auto-refreshes 30s</span>
                        <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                      </div>
                    </div>

                    {/* Notification list */}
                    <div className="max-h-[420px] overflow-y-auto">
                      {notifications.length === 0 ? (
                        <div className="py-10 text-center">
                          <Bell size={28} className="text-slate-700 mx-auto mb-2" />
                          <p className="text-slate-600 text-xs font-bold">No high-confidence signals right now</p>
                          <p className="text-slate-700 text-[10px] mt-1">Model alerts appear here when confidence ≥ 65%</p>
                        </div>
                      ) : notifications.map(n => (
                        <div key={n.id} className={`px-4 py-3 border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors ${n.decision === 'BUY' ? 'border-l-2 border-l-emerald-500/60' : 'border-l-2 border-l-rose-500/60'}`}>
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-2">
                              <span className={`text-[9px] font-black px-2 py-0.5 rounded ${n.decision === 'BUY' ? 'bg-emerald-500 text-black' : 'bg-rose-500 text-white'}`}>
                                {n.decision}
                              </span>
                              <span className="text-sm font-black text-white">{n.symbol}</span>
                            </div>
                            <div className="text-right">
                              <div className="text-[10px] font-black text-white">{Math.round((n.confidence || 0) * 100)}%</div>
                              <div className="text-[8px] text-slate-600">confidence</div>
                            </div>
                          </div>
                          {/* Price levels */}
                          <div className="grid grid-cols-3 gap-1 mt-2">
                            <div className="text-center">
                              <div className="text-[8px] text-slate-600 font-bold">ENTRY</div>
                              <div className="text-[10px] font-black text-white">{n.price ? Number(n.price).toFixed(2) : '—'}</div>
                            </div>
                            <div className="text-center">
                              <div className="text-[8px] text-rose-600 font-bold">SL</div>
                              <div className="text-[10px] font-black text-rose-300">{n.sl ? Number(n.sl).toFixed(2) : '—'}</div>
                            </div>
                            <div className="text-center">
                              <div className="text-[8px] text-emerald-600 font-bold">TP</div>
                              <div className="text-[10px] font-black text-emerald-300">{n.tp ? Number(n.tp).toFixed(2) : '—'}</div>
                            </div>
                          </div>
                          {/* Target qualifier badge */}
                          {n.target_status === 'MEETS_TARGET' && (
                            <div className="mt-1.5 text-[9px] text-emerald-400 font-black">✅ Meets your {n.target_label} target</div>
                          )}
                          {n.target_status === 'BELOW_TARGET' && (
                            <div className="mt-1.5 text-[9px] text-amber-500 font-black">⚠️ Below {n.target_label} target</div>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* Footer */}
                    <div className="px-4 py-2.5 bg-slate-950/50 border-t border-slate-800 flex justify-between items-center">
                      <span className="text-[9px] text-slate-600">Only BUY/SELL signals ≥ 65% confidence shown</span>
                      <button onClick={() => { setActiveTab('radar'); setShowNotifications(false); }}
                        className="text-[9px] text-primary font-black hover:underline">View All →</button>
                    </div>
                  </div>
                )}
              </div>
              <div className="h-8 w-px bg-slate-800"></div>
              <div className="flex items-center gap-3 cursor-pointer group" onClick={() => setShowSettings(true)}>
                <div className="text-right hidden sm:block">
                  <p className="text-xs font-bold text-white group-hover:text-primary transition-colors">{user.name}</p>
                  <p className="text-[10px] font-medium text-slate-500 uppercase tracking-tighter">Verified Trader</p>
                </div>
                <div className="size-10 rounded-full border-2 border-primary/20 overflow-hidden group-hover:border-primary transition-all shadow-lg flex items-center justify-center bg-primary/10 text-primary font-black">
                  {user.picture ? (
                    <img src={user.picture} alt={user.name} className="w-full h-full object-cover" />
                  ) : (
                    user.name.split(' ').map(n => n[0]).join('').toUpperCase()
                  )}
                </div>
              </div>
            </div>
          </header>

          {/* Settings Modal */}
          {showSettings && (
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex flex-col justify-center items-center p-4">
              <div className="bg-[#0f172a] border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
                <div className="flex justify-between items-center p-6 border-b border-slate-800 bg-slate-900/50">
                  <h2 className="text-xl font-black text-white flex items-center gap-2"><Settings size={20} className="text-primary" /> Application Profile & Settings</h2>
                  <button onClick={() => setShowSettings(false)} className="text-slate-500 hover:text-white transition-colors"><X size={20} /></button>
                </div>
                <div className="p-6 grid grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <div>
                      <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-widest">Full Name</label>
                      <input type="text" readOnly value={user.name} className="w-full bg-slate-950 border border-slate-800 py-2.5 px-3 rounded-lg text-white font-semibold opacity-70" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-widest">Email Address</label>
                      <input type="text" readOnly value={user.email} className="w-full bg-slate-950 border border-slate-800 py-2.5 px-3 rounded-lg text-white font-semibold opacity-70" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-widest">Global Theme</label>
                      <div className="flex gap-2">
                        <button className="flex-1 bg-primary text-white py-2 rounded-lg text-xs font-bold">Dark Mode</button>
                        <button className="flex-1 bg-slate-800 text-slate-400 py-2 rounded-lg text-xs font-bold cursor-not-allowed opacity-50">Light Mode (Pro)</button>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-6">
                    <div>
                      <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-widest">System Status: Active</label>
                      <div className="bg-slate-950 p-4 border border-slate-800 rounded-lg space-y-3">
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-slate-400">Trading Agents</span>
                          <span className="text-emerald-400 font-bold">● Online</span>
                        </div>
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-slate-400">Live Radar Loop</span>
                          <span className="text-emerald-400 font-bold">● Running</span>
                        </div>
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-slate-400">Database Connection</span>
                          <span className="text-primary font-bold">PostgreSQL</span>
                        </div>
                      </div>
                    </div>
                    <div>
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center justify-center gap-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 py-3 rounded-lg font-bold transition-colors"
                      >
                        <LogOut size={16} /> Secure Sign Out
                      </button>
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-slate-900 border-t border-slate-800 text-center">
                  <button onClick={() => setShowSettings(false)} className="bg-emerald-500 hover:bg-emerald-600 text-black font-black px-8 py-2.5 rounded-lg transition-colors shadow-lg">Save Preferences</button>
                </div>
              </div>
            </div>
          )}

          {/* View Area */}
          <div className="flex-1 overflow-y-auto overflow-x-hidden no-scrollbar bg-[radial-gradient(circle_at_top_right,rgba(19,109,236,0.05),transparent)]">
            {activeTab === 'sip' ? (
              <SIPPlannerView />
            ) : activeTab === 'discover' && !data ? (
              <MarketExplorerView onSelectAsset={(t, s) => { setAssetType(t); setSymbol(s); fetchData(null, t, s); }} />
            ) : activeTab === 'terminal' ? (
              <TerminalView data={data} />
            ) : activeTab === 'radar' ? (
              <RadarView />
            ) : activeTab === 'journal' ? (
              <TradeJournalView />
            ) : activeTab === 'portfolio' ? (
              <PortfolioView />
            ) : (
              <div className="p-8">
                {loading && (
                  <div className="flex flex-col items-center justify-center h-[60vh] gap-6">
                    <div className="size-16 border-4 border-slate-800 border-t-primary rounded-full animate-spin"></div>
                    <div className="text-center">
                      <h3 className="text-xl font-bold text-white mb-2">Neural Engine Processing</h3>
                      <p className="text-slate-500 font-medium">Aggregating cross-market signals and alternative data sets...</p>
                    </div>
                  </div>
                )}

                {error && (
                  <div className="max-w-xl mx-auto mt-20 p-6 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center gap-4 text-rose-400">
                    <AlertCircle size={32} />
                    <div>
                      <h4 className="font-bold">Institutional Data Error</h4>
                      <p className="text-sm opacity-80">{error}</p>
                    </div>
                  </div>
                )}

                {!loading && data && (
                  <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="flex justify-between items-end">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="px-2 py-0.5 rounded-full bg-primary/20 text-primary text-[10px] font-black tracking-widest uppercase">Verified Alpha</span>
                          <span className="text-xs font-bold text-slate-500">{data.latest_indicators?.timestamp || new Date().toISOString()}</span>
                        </div>
                        <h2 className="text-5xl font-black text-white tracking-tighter">{data.symbol}</h2>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Indicative Price</p>
                        <h3 className="text-4xl font-black text-white">${(data.latest_indicators?.close || data.forecast?.current_nav || 0).toFixed(2)}</h3>
                      </div>
                    </div>

                    {data.risk_intelligence && data.forecast ? (
                      <MutualFundView data={data} />
                    ) : (
                      <div className="grid grid-cols-12 gap-8">
                        <div className="col-span-12">
                          <div className="h-[500px] w-full">
                            <TradingViewChart symbol={data.tv_symbol || data.symbol} />
                          </div>
                        </div>
                        <div className="col-span-12 lg:col-span-8">
                          <AgentPanel data={data} />
                        </div>
                        <div className="col-span-12 lg:col-span-4">
                          <RiskCard data={data} onRefresh={() => fetchData(null, assetType, symbol)} />
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </GoogleOAuthProvider>
  );
}

export default App;
