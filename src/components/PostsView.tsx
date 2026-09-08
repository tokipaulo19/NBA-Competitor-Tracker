import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  LineChart, Line,
} from 'recharts';
import type { DashboardData } from '../data/dataService';

interface Props {
  data: DashboardData;
}

export default function PostsView({ data }: Props) {
  const { weeklyReport } = data;

  // Post frequency data from weekly report
  const postData = weeklyReport
    .map(r => ({
      handle: r.handle,
      totalPosts: r.current_total_posts,
      newPosts: r.posts_since_previous_snapshot,
      comparisonDays: r.comparison_days,
    }))
    .sort((a, b) => b.newPosts - a.newPosts);

  // Calculate posting rate (posts per week)
  const postingRate = weeklyReport.map(r => {
    const days = r.comparison_days || 7;
    const weeks = days / 7;
    const rate = weeks > 0 ? r.posts_since_previous_snapshot / weeks : 0;
    return {
      handle: r.handle,
      rate: Math.round(rate * 10) / 10,
      newPosts: r.posts_since_previous_snapshot,
      days,
    };
  }).sort((a, b) => b.rate - a.rate);

  // Top posters
  const totalNewPosts = postData.reduce((sum, p) => sum + p.newPosts, 0);

  // Historical post data
  const historicalPostData = data.historical
    .filter(r => r.handle === 'nbaaustralia_official')
    .map(r => ({ date: r.date, posts: r.published_content }));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Post Activity</h2>
        <p className="text-gray-500 text-sm mt-1">
          Track posting frequency and content output across competitors
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-5">
          <p className="text-xs text-gray-500 font-medium">Total New Posts (All Accounts)</p>
          <p className="text-2xl font-bold text-white mt-1">{totalNewPosts}</p>
          <p className="text-xs text-gray-600 mt-1">Since last snapshot period</p>
        </div>
        <div className="bg-[#1a1a1a] border border-[#E3B100]/20 rounded-2xl p-5">
          <p className="text-xs text-gray-500 font-medium">Most Active</p>
          <p className="text-2xl font-bold text-white mt-1">@{postData[0]?.handle}</p>
          <p className="text-xs text-[#E3B100] mt-1">+{postData[0]?.newPosts} posts</p>
        </div>
        <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-5">
          <p className="text-xs text-gray-500 font-medium">NBA New Posts</p>
          <p className="text-2xl font-bold text-white mt-1">
            +{weeklyReport.find(r => r.handle === 'nbaaustralia_official')?.posts_since_previous_snapshot || 0}
          </p>
          <p className="text-xs text-gray-600 mt-1">This period</p>
        </div>
      </div>

      {/* New Posts Bar Chart */}
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-4 sm:p-6">
        <h3 className="text-lg font-semibold text-white mb-1">New Posts Since Last Snapshot</h3>
        <p className="text-sm text-gray-500 mb-4">Ranked by posting activity</p>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={postData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
            <XAxis type="number" stroke="#666" fontSize={11} />
            <YAxis type="category" dataKey="handle" stroke="#666" fontSize={10} width={140} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: '8px', fontSize: '12px' }}
              formatter={(value: number) => [`${value} posts`, '']}
            />
            <Bar dataKey="newPosts" radius={[0, 4, 4, 0]}>
              {postData.map((entry) => {
                const isNBA = entry.handle === 'nbaaustralia_official';
                return (
                  <Cell
                    key={entry.handle}
                    fill={isNBA ? '#E3B100' : '#ffffff'}
                    opacity={isNBA ? 1 : 0.4}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Posting Rate */}
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-4 sm:p-6">
        <h3 className="text-lg font-semibold text-white mb-1">Posting Rate (Posts per Week)</h3>
        <p className="text-sm text-gray-500 mb-4">Normalized by comparison period length</p>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={postingRate} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
            <XAxis type="number" stroke="#666" fontSize={11} tickFormatter={(v) => `${v}/wk`} />
            <YAxis type="category" dataKey="handle" stroke="#666" fontSize={10} width={140} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: '8px', fontSize: '12px' }}
              formatter={(value: number) => [`${value} posts/week`, '']}
            />
            <Bar dataKey="rate" radius={[0, 4, 4, 0]}>
              {postingRate.map((entry) => {
                const isNBA = entry.handle === 'nbaaustralia_official';
                return (
                  <Cell
                    key={entry.handle}
                    fill={isNBA ? '#E3B100' : '#ffffff'}
                    opacity={isNBA ? 1 : 0.3}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* NBA Post History from Historical Data */}
      {historicalPostData.length > 0 && (
        <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-4 sm:p-6">
          <h3 className="text-lg font-semibold text-white mb-1">NBA - Published Content History</h3>
          <p className="text-sm text-gray-500 mb-4">From manually collected historical data</p>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={historicalPostData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis dataKey="date" stroke="#666" fontSize={10} />
              <YAxis stroke="#666" fontSize={10} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: '8px', fontSize: '12px' }}
                formatter={(value: number) => [value.toLocaleString(), 'Posts']}
              />
              <Line type="monotone" dataKey="posts" stroke="#E3B100" strokeWidth={3} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}