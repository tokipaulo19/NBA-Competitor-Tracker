import { LayoutDashboard, Trophy, TrendingUp, FileText, Menu, X } from 'lucide-react';
import { useState } from 'react';

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
  lastFetch: Date | null;
  onRefresh: () => void;
  loading: boolean;
}

const navItems = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
  { id: 'rankings', label: 'Rankings', icon: Trophy },
  { id: 'growth', label: 'Growth', icon: TrendingUp },
  { id: 'posts', label: 'Posts', icon: FileText },
];

export default function Sidebar({ activeView, onViewChange, lastFetch, onRefresh, loading }: SidebarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleNav = (view: string) => {
    onViewChange(view);
    setMobileOpen(false);
  };

  return (
    <>
      {/* Mobile toggle button */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg"
      >
        {mobileOpen ? <X size={20} className="text-white" /> : <Menu size={20} className="text-white" />}
      </button>

      {/* Overlay for mobile */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-40
        w-64 bg-[#111] border-r border-[#2a2a2a] flex flex-col
        transform transition-transform duration-200 ease-in-out
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Logo */}
        <div className="p-6 border-b border-[#2a2a2a]">
        <img 
          src="https://raw.githubusercontent.com/tokipaulo19/nbaaustralia-operations/main/assets/NBA%20logo.png" 
          alt="NBA Logo" 
          className="w-full h-auto max-h-20 object-contain"
        />        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNav(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? 'bg-[#E3B100] text-black'
                    : 'text-gray-400 hover:bg-[#1a1a1a] hover:text-white'
                }`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-[#2a2a2a]">
          <button
            onClick={onRefresh}
            disabled={loading}
            className="w-full px-4 py-2 bg-[#1a1a1a] hover:bg-[#2a2a2a] text-gray-300 rounded-lg text-sm font-medium transition disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Refresh Data'}
          </button>
          {lastFetch && (
            <p className="text-xs text-gray-500 mt-2 text-center">
              Last updated: {lastFetch.toLocaleTimeString()}
            </p>
          )}
        </div>
      </aside>
    </>
  );
}