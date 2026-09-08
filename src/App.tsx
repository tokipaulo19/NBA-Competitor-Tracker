import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import RankingsView from './components/RankingsView';
import GrowthView from './components/GrowthView';
import PostsView from './components/PostsView';
import { fetchDashboardData, type DashboardData } from './data/dataService';

export default function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchDashboardData();
      setData(result);
      setLastFetch(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const renderView = () => {
    if (loading && !data) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-[#E3B100] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Loading data from GitHub...</p>
          </div>
        </div>
      );
    }

    if (error && !data) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center max-w-md">
            <div className="text-4xl mb-4">⚠️</div>
            <p className="text-white font-semibold mb-2">Failed to load data</p>
            <p className="text-gray-400 text-sm mb-4">{error}</p>
            <button
              onClick={loadData}
              className="px-4 py-2 bg-[#E3B100] hover:bg-[#c99b00] text-black rounded-lg text-sm font-medium transition"
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    if (!data) return null;

    switch (activeView) {
      case 'dashboard':
        return <Dashboard data={data} />;
      case 'rankings':
        return <RankingsView data={data} />;
      case 'growth':
        return <GrowthView data={data} />;
      case 'posts':
        return <PostsView data={data} />;
      default:
        return <Dashboard data={data} />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-950 text-white overflow-hidden relative">
      <div 
        className="fixed inset-0 pointer-events-none opacity-[0.03] bg-center bg-no-repeat bg-contain z-0"
        style={{
          backgroundImage: 'url(https://raw.githubusercontent.com/tokipaulo19/nbaaustralia-operations/main/assets/NBA%20logo.png)'
        }}
      />
      
      <div className="flex w-full relative z-10">
        <Sidebar
          activeView={activeView}
          onViewChange={setActiveView}
          lastFetch={lastFetch}
          onRefresh={loadData}
          loading={loading}
        />
        <main className="flex-1 overflow-y-auto">
          <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto pt-16 lg:pt-8">
            {renderView()}
          </div>
        </main>
      </div>
    </div>
  );
}