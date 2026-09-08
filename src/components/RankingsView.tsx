import { TrendingUp, TrendingDown, ExternalLink } from 'lucide-react';
import type { DashboardData } from '../data/dataService';

interface Props {
  data: DashboardData;
}

export default function RankingsView({ data }: Props) {
  const { weeklyReport, competitors } = data;

  const formatNumber = (num: number) => num.toLocaleString();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Competitor Rankings</h2>
        <p className="text-gray-500 text-sm mt-1">
          Ranked by followers - Report date: {data.lastUpdated}
        </p>
      </div>

      {/* Full Rankings Table */}
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#2a2a2a] bg-[#111]">
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-3 sm:px-6 py-3 sm:py-4">Rank</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-3 sm:px-6 py-3 sm:py-4">Account</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-3 sm:px-6 py-3 sm:py-4">Followers</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-3 sm:px-6 py-3 sm:py-4">Change (30d)</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-3 sm:px-6 py-3 sm:py-4">Growth %</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-3 sm:px-6 py-3 sm:py-4">Total Posts</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-3 sm:px-6 py-3 sm:py-4">New Posts</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-3 sm:px-6 py-3 sm:py-4"></th>
              </tr>
            </thead>
            <tbody>
              {weeklyReport.map((row) => {
                const comp = competitors.find(c => c.handle === row.handle);
                const isNBA = row.handle === 'nbaaustralia_official';
                return (
                  <tr
                    key={row.handle}
                    className={`border-b border-[#2a2a2a] hover:bg-[#2a2a2a]/50 transition ${isNBA ? 'bg-[#E3B100]/5' : ''}`}
                  >
                    <td className="px-3 sm:px-6 py-3 sm:py-4">
                      <div className={`flex items-center justify-center w-8 h-8 rounded-lg font-bold text-sm ${
                        row.rank === 1 ? 'bg-[#E3B100]/20 text-[#E3B100]' :
                        row.rank === 2 ? 'bg-gray-400/20 text-gray-300' :
                        row.rank === 3 ? 'bg-orange-500/20 text-orange-400' :
                        isNBA ? 'bg-[#E3B100]/20 text-[#E3B100]' :
                        'bg-[#2a2a2a] text-gray-400'
                      }`}>
                        {row.rank}
                      </div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4">
                      <div>
                        <p className={`text-xs sm:text-sm font-medium ${isNBA ? 'text-[#E3B100]' : 'text-white'}`}>
                          @{row.handle}
                          {isNBA && <span className="ml-2 text-xs bg-[#E3B100]/20 text-[#E3B100] px-1.5 py-0.5 rounded">NBA</span>}
                        </p>
                        {comp && <p className="text-xs text-gray-500 hidden sm:block">{comp.name}</p>}
                      </div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4">
                      <p className="text-xs sm:text-sm font-semibold text-white">{formatNumber(row.current_followers)}</p>
                      <p className="text-xs text-gray-600 hidden sm:block">vs {formatNumber(row.comparison_followers)}</p>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4">
                      <div className={`flex items-center gap-1 text-xs sm:text-sm font-medium ${row.follower_change_30d_plus >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {row.follower_change_30d_plus >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                        <span>{row.follower_change_30d_plus >= 0 ? '+' : ''}{formatNumber(row.follower_change_30d_plus)}</span>
                      </div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-12 sm:w-16 h-2 bg-[#2a2a2a] rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${row.growth_percent_30d_plus >= 0 ? 'bg-green-500' : 'bg-red-500'}`}
                            style={{ width: `${Math.min(Math.abs(row.growth_percent_30d_plus) * 10, 100)}%` }}
                          />
                        </div>
                        <span className={`text-xs ${row.growth_percent_30d_plus >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {row.growth_percent_30d_plus >= 0 ? '+' : ''}{row.growth_percent_30d_plus}%
                        </span>
                      </div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4">
                      <p className="text-xs sm:text-sm text-gray-300">{formatNumber(row.current_total_posts)}</p>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4">
                      <p className="text-xs sm:text-sm text-gray-300">+{row.posts_since_previous_snapshot}</p>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4">
                      <a
                        href={comp?.profile_url || `https://instagram.com/${row.handle}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 hover:bg-[#2a2a2a] rounded-lg transition inline-block"
                      >
                        <ExternalLink size={14} className="text-gray-500" />
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Ahead/Behind NBA */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Ahead of NBA</h3>
          <div className="space-y-3">
            {weeklyReport.filter(r => r.ahead_of_nba === 'yes' && r.handle !== 'nbaaustralia_official').map(r => (
              <div key={r.handle} className="flex items-center justify-between p-3 bg-[#111] rounded-xl border border-[#2a2a2a]">
                <div>
                  <p className="text-sm font-medium text-white">@{r.handle}</p>
                  <p className="text-xs text-gray-500">{formatNumber(r.current_followers)} followers</p>
                </div>
                <span className="text-sm font-semibold text-green-400">
                  +{formatNumber(r.current_followers - (weeklyReport.find(w => w.handle === 'nbaaustralia_official')?.current_followers || 0))}
                </span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Behind NBA</h3>
          <div className="space-y-3">
            {weeklyReport.filter(r => r.ahead_of_nba === 'no' && r.handle !== 'nbaaustralia_official').slice(0, 5).map(r => {
              const nbaFollowers = weeklyReport.find(w => w.handle === 'nbaaustralia_official')?.current_followers || 0;
              return (
                <div key={r.handle} className="flex items-center justify-between p-3 bg-[#111] rounded-xl border border-[#2a2a2a]">
                  <div>
                    <p className="text-sm font-medium text-white">@{r.handle}</p>
                    <p className="text-xs text-gray-500">{formatNumber(r.current_followers)} followers</p>
                  </div>
                  <span className="text-sm font-semibold text-red-400">
                    -{formatNumber(nbaFollowers - r.current_followers)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}