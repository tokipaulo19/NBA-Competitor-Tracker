import { Trophy, TrendingUp, TrendingDown, FileText } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { DashboardData } from '../data/dataService';

interface Props {
  data: DashboardData;
}

export default function Dashboard({ data }: Props) {
  const { weeklyReport, snapshots } = data;

  const latestDate = snapshots.length > 0
    ? snapshots.reduce((latest, s) => s.date > latest ? s.date : latest, snapshots[0].date)
    : '';

  const nbaRank = weeklyReport.find(r => r.handle === 'nbaaustralia_official');
  const nbaFollowers = nbaRank?.current_followers || 0;

  // Top grower (excluding NBA)
  const topGrower = weeklyReport
    .filter(r => r.handle !== 'nbaaustralia_official')
    .reduce((top, r) => r.growth_percent_30d_plus > top.growth_percent_30d_plus ? r : top, weeklyReport[1]);

  // Most active poster (excluding NBA)
  const topPoster = weeklyReport
    .filter(r => r.handle !== 'nbaaustralia_official')
    .reduce((top, r) => r.posts_since_previous_snapshot > top.posts_since_previous_snapshot ? r : top, weeklyReport[1]);

  // Build chart data for top 5 accounts
  const top5 = weeklyReport.slice(0, 5);
  const chartData = buildTopAccountsChart(data, top5.map(r => r.handle));

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">Overview</h2>
        <p className="text-gray-500 text-sm mt-1">
          Tracking {data.competitors.filter(c => c.active).length} competitors - Data as of {data.lastUpdated || latestDate}
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="NBA Followers"
          value={formatNumber(nbaFollowers)}
          icon={Trophy}
        />
        <MetricCard
          title="NBA Rank"
          value={nbaRank ? `#${nbaRank.rank}` : 'N/A'}
          subtitle={nbaRank?.growth_percent_30d_plus !== undefined ? `${nbaRank.growth_percent_30d_plus >= 0 ? '+' : ''}${nbaRank.growth_percent_30d_plus}% (30d)` : ''}
          icon={TrendingUp}
        />
        <MetricCard
          title="Top Grower (30d)"
          value={topGrower ? `@${topGrower.handle}` : 'N/A'}
          subtitle={topGrower ? `+${topGrower.growth_percent_30d_plus}%` : ''}
          icon={TrendingUp}
        />
        <MetricCard
          title="Most Active Poster"
          value={topPoster ? `@${topPoster.handle}` : 'N/A'}
          subtitle={topPoster ? `+${topPoster.posts_since_previous_snapshot} posts` : ''}
          icon={FileText}
        />
      </div>

      {/* Top 5 Follower Growth Chart */}
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-4 sm:p-6">
        <h3 className="text-lg font-semibold text-white mb-1">Top 5 Accounts - Follower Trend</h3>
        <p className="text-sm text-gray-500 mb-4">Historical + automated snapshot data</p>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
            <XAxis dataKey="date" stroke="#666" fontSize={11} />
            <YAxis stroke="#666" fontSize={11} tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: '8px', fontSize: '12px' }}
              formatter={(value: number) => [value.toLocaleString(), '']}
            />
            <Legend />
            {top5.map((account, index) => {
              const isNBA = account.handle === 'nbaaustralia_official';
              const colors = ['#E3B100', '#ffffff', '#888888', '#666666', '#444444'];
              return (
                <Line
                  key={account.handle}
                  type="monotone"
                  dataKey={account.handle}
                  stroke={isNBA ? '#E3B100' : colors[index]}
                  strokeWidth={isNBA ? 3 : 2}
                  dot={{ r: 3 }}
                  name={account.handle}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Quick Rankings Table */}
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-[#2a2a2a]">
          <h3 className="text-lg font-semibold text-white">Current Rankings</h3>
          <p className="text-sm text-gray-500">Based on latest weekly report ({data.lastUpdated || latestDate})</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#2a2a2a]">
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Rank</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Account</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Followers</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Growth (30d)</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-6 py-3">Posts</th>
              </tr>
            </thead>
            <tbody>
              {weeklyReport.slice(0, 10).map((row) => {
                const isNBA = row.handle === 'nbaaustralia_official';
                return (
                  <tr key={row.handle} className={`border-b border-[#2a2a2a] ${isNBA ? 'bg-[#E3B100]/5' : ''} hover:bg-[#2a2a2a]/50 transition`}>
                    <td className="px-6 py-3">
                      <span className={`text-sm font-bold ${isNBA ? 'text-[#E3B100]' : 'text-gray-300'}`}>
                        #{row.rank}
                      </span>
                    </td>
                    <td className="px-6 py-3">
                      <p className={`text-sm font-medium ${isNBA ? 'text-[#E3B100]' : 'text-white'}`}>
                        @{row.handle}
                        {isNBA && <span className="ml-2 text-xs bg-[#E3B100]/20 text-[#E3B100] px-1.5 py-0.5 rounded">NBA</span>}
                      </p>
                    </td>
                    <td className="px-6 py-3">
                      <p className="text-sm font-semibold text-white">{row.current_followers.toLocaleString()}</p>
                    </td>
                    <td className="px-6 py-3">
                      <div className={`flex items-center gap-1 text-sm ${row.growth_percent_30d_plus >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {row.growth_percent_30d_plus >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                        <span>{row.growth_percent_30d_plus >= 0 ? '+' : ''}{row.growth_percent_30d_plus}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-3">
                      <p className="text-sm text-gray-300">{row.current_total_posts.toLocaleString()}</p>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, subtitle, icon: Icon }: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ElementType;
}) {
  return (
    <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs text-gray-500 font-medium truncate">{title}</p>
          <p className="text-lg sm:text-xl font-bold text-white mt-1 truncate">{value}</p>
          {subtitle && <p className="text-xs text-[#E3B100] mt-1 truncate">{subtitle}</p>}
        </div>
        <div className="p-2 sm:p-2.5 rounded-xl bg-[#E3B100]/10 border border-[#E3B100]/20 shrink-0">
          <Icon size={16} className="text-[#E3B100]" />
        </div>
      </div>
    </div>
  );
}

function buildTopAccountsChart(data: DashboardData, handles: string[]) {
  const dateMap = new Map<string, Record<string, number | string>>();

  data.historical.forEach(r => {
    if (!handles.includes(r.handle)) return;
    if (!dateMap.has(r.date)) dateMap.set(r.date, { date: r.date });
    const entry = dateMap.get(r.date)!;
    entry[r.handle] = r.followers;
  });

  data.snapshots.forEach(r => {
    if (!handles.includes(r.handle)) return;
    if (!dateMap.has(r.date)) dateMap.set(r.date, { date: r.date });
    const entry = dateMap.get(r.date)!;
    entry[r.handle] = r.followers;
  });

  return Array.from(dateMap.values()).sort((a, b) =>
    String(a.date).localeCompare(String(b.date))
  );
}