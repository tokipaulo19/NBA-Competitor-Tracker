import { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  BarChart, Bar, Cell,
} from 'recharts';
import type { DashboardData } from '../data/dataService';
import { buildTimeline } from '../data/dataService';

interface Props {
  data: DashboardData;
}

export default function GrowthView({ data }: Props) {
  const { competitors, weeklyReport } = data;
  const [selectedHandles, setSelectedHandles] = useState<string[]>([
    'nbaaustralia_official',
    'ifbbproleagueoz',
    'icnqld',
    'nabbaaustralia',
    'msfitnessaustralia',
  ]);

  const toggleHandle = (handle: string) => {
    setSelectedHandles(prev =>
      prev.includes(handle)
        ? prev.filter(h => h !== handle)
        : [...prev, handle]
    );
  };

  // Build timeline chart data
  const dateMap = new Map<string, Record<string, number | string>>();

  data.historical.forEach(r => {
    if (!dateMap.has(r.date)) dateMap.set(r.date, { date: r.date });
    const entry = dateMap.get(r.date)!;
    entry[r.handle] = r.followers;
  });

  data.snapshots.forEach(r => {
    if (!dateMap.has(r.date)) dateMap.set(r.date, { date: r.date });
    const entry = dateMap.get(r.date)!;
    entry[r.handle] = r.followers;
  });

  const chartData = Array.from(dateMap.values()).sort((a, b) =>
    String(a.date).localeCompare(String(b.date))
  );

  // Growth comparison bar chart
  const growthData = weeklyReport
    .map(r => ({
      handle: r.handle,
      growth: r.growth_percent_30d_plus,
      change: r.follower_change_30d_plus,
    }))
    .sort((a, b) => b.growth - a.growth);

  // NBA position over time
  const nbaTimeline = buildTimeline(data, 'nbaaustralia_official');

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Follower Growth</h2>
        <p className="text-gray-500 text-sm mt-1">Track follower changes over time across all competitors</p>
      </div>

      {/* Account Selector */}
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-4">
        <p className="text-sm text-gray-500 mb-3">Select accounts to compare:</p>
        <div className="flex flex-wrap gap-1.5 sm:gap-2">
          {competitors.filter(c => c.active).map(comp => {
            const isSelected = selectedHandles.includes(comp.handle);
            const isNBA = comp.handle === 'nbaaustralia_official';
            return (
              <button
                key={comp.handle}
                onClick={() => toggleHandle(comp.handle)}
                className={`px-2 sm:px-3 py-1 sm:py-1.5 text-[10px] sm:text-xs font-medium rounded-full border transition ${
                  isSelected
                    ? isNBA
                      ? 'bg-[#E3B100]/20 border-[#E3B100]/40 text-[#E3B100]'
                      : 'bg-white/10 border-white/20 text-white'
                    : 'bg-[#111] border-[#2a2a2a] text-gray-500 hover:text-gray-300'
                }`}
              >
                @{comp.handle}
              </button>
            );
          })}
        </div>
      </div>

      {/* Multi-Account Growth Chart */}
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-4 sm:p-6">
        <h3 className="text-lg font-semibold text-white mb-1">Follower Growth Over Time</h3>
        <p className="text-sm text-gray-500 mb-4">Combined historical + automated data</p>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
            <XAxis dataKey="date" stroke="#666" fontSize={11} />
            <YAxis stroke="#666" fontSize={11} tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: '8px', fontSize: '12px' }}
              formatter={(value: number) => [value.toLocaleString(), '']}
            />
            <Legend />
            {selectedHandles.map(handle => {
              const isNBA = handle === 'nbaaustralia_official';
              return (
                <Line
                  key={handle}
                  type="monotone"
                  dataKey={handle}
                  stroke={isNBA ? '#E3B100' : '#ffffff'}
                  strokeWidth={isNBA ? 3 : 2}
                  dot={{ r: 3 }}
                  name={handle}
                  strokeOpacity={isNBA ? 1 : 0.5}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Growth % Bar Chart */}
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-4 sm:p-6">
        <h3 className="text-lg font-semibold text-white mb-1">30-Day Growth %</h3>
        <p className="text-sm text-gray-500 mb-4">Ranked by growth percentage</p>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={growthData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
            <XAxis type="number" stroke="#666" fontSize={11} tickFormatter={(v) => `${v}%`} />
            <YAxis type="category" dataKey="handle" stroke="#666" fontSize={10} width={140} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: '8px', fontSize: '12px' }}
              formatter={(value: number) => [`${value}%`, 'Growth']}
            />
            <Bar dataKey="growth" radius={[0, 4, 4, 0]}>
              {growthData.map((entry) => {
                const isNBA = entry.handle === 'nbaaustralia_official';
                return (
                  <Cell
                    key={entry.handle}
                    fill={isNBA ? '#E3B100' : entry.growth >= 0 ? '#4ade80' : '#f87171'}
                    opacity={isNBA ? 1 : 0.6}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* NBA Growth Detail */}
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-white mb-1">NBA Australia - Growth Detail</h3>
        <p className="text-sm text-gray-500 mb-4">Follower count over time</p>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={nbaTimeline}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
            <XAxis dataKey="date" stroke="#666" fontSize={10} />
            <YAxis stroke="#666" fontSize={10} tickFormatter={(v) => `${(v / 1000).toFixed(1)}K`} domain={['dataMin - 200', 'dataMax + 200']} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: '8px', fontSize: '12px' }}
              formatter={(value: number) => [value.toLocaleString(), 'Followers']}
            />
            <Line type="monotone" dataKey="followers" stroke="#E3B100" strokeWidth={3} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}