export interface Competitor {
  handle: string;
  name: string;
  profile_url: string;
  active: boolean;
}

export interface HistoricalRecord {
  date: string;
  handle: string;
  followers: number;
  published_content: number;
  source: string;
}

export interface Snapshot {
  date: string;
  handle: string;
  followers: number;
  total_posts: number;
  status: string;
  source: string;
}

export interface WeeklyReportRow {
  rank: number;
  handle: string;
  current_followers: number;
  comparison_followers: number;
  follower_change_30d_plus: number;
  growth_percent_30d_plus: number;
  comparison_date: string;
  comparison_days: number;
  comparison_source: string;
  current_total_posts: number;
  posts_since_previous_snapshot: number;
  previous_post_snapshot_date: string;
  ahead_of_nba: string;
}

export interface DashboardData {
  competitors: Competitor[];
  historical: HistoricalRecord[];
  snapshots: Snapshot[];
  weeklyReport: WeeklyReportRow[];
  lastUpdated: string;
}

const BASE_URL = 'https://raw.githubusercontent.com/tokipaulo19/nbaaustralia-operations/main';

function parseCSV(text: string): string[][] {
  const lines = text.trim().split('\n');
  return lines.map(line => {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    result.push(current.trim());
    return result;
  });
}

export async function fetchDashboardData(): Promise<DashboardData> {
  try {
    const [competitorsRes, historicalRes, snapshotsRes, weeklyReportRes] = await Promise.all([
      fetch(`${BASE_URL}/config/competitors.csv`),
      fetch(`${BASE_URL}/data/historical.csv`),
      fetch(`${BASE_URL}/data/instagram_snapshots.csv`),
      fetch(`${BASE_URL}/data/weekly_report.csv`)
    ]);

    const [competitorsText, historicalText, snapshotsText, weeklyReportText] = await Promise.all([
      competitorsRes.text(),
      historicalRes.text(),
      snapshotsRes.text(),
      weeklyReportRes.text()
    ]);

    // Parse competitors
    const competitorsRows = parseCSV(competitorsText);
    const competitors: Competitor[] = competitorsRows.slice(1).map(row => ({
      handle: row[0],
      name: row[1],
      profile_url: row[2],
      active: row[4] === 'yes'
    }));

    // Parse historical data
    const historicalRows = parseCSV(historicalText);
    const historical: HistoricalRecord[] = historicalRows.slice(1).map(row => ({
      date: row[0],
      handle: row[1],
      followers: parseInt(row[2]) || 0,
      published_content: parseInt(row[3]) || 0,
      source: row[4]
    }));

    // Parse snapshots
    const snapshotsRows = parseCSV(snapshotsText);
    const snapshots: Snapshot[] = snapshotsRows.slice(1).map(row => ({
      date: row[0],
      handle: row[2],
      followers: parseInt(row[3]) || 0,
      total_posts: parseInt(row[5]) || 0,
      status: row[6],
      source: row[7]
    }));

    // Parse weekly report
    const weeklyReportRows = parseCSV(weeklyReportText);
    const weeklyReport: WeeklyReportRow[] = weeklyReportRows.slice(1).map(row => ({
      rank: parseInt(row[1]) || 0,
      handle: row[2],
      current_followers: parseInt(row[3]) || 0,
      comparison_followers: parseInt(row[4]) || 0,
      follower_change_30d_plus: parseInt(row[5]) || 0,
      growth_percent_30d_plus: parseFloat(row[6]) || 0,
      comparison_date: row[7],
      comparison_days: parseInt(row[8]) || 0,
      comparison_source: row[9],
      current_total_posts: parseInt(row[10]) || 0,
      posts_since_previous_snapshot: parseInt(row[11]) || 0,
      previous_post_snapshot_date: row[12],
      ahead_of_nba: row[13]
    }));

    // Get last updated date from snapshots
    const lastUpdated = snapshots.length > 0
      ? snapshots.reduce((latest, s) => s.date > latest ? s.date : latest, snapshots[0].date)
      : '';

    return {
      competitors,
      historical,
      snapshots,
      weeklyReport,
      lastUpdated
    };
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error);
    throw error;
  }
}

export function buildTimeline(data: DashboardData, handle: string) {
  const dateMap = new Map<string, { date: string; followers: number; total_posts: number }>();

  // Add historical data
  data.historical.forEach(r => {
    if (r.handle !== handle) return;
    if (!dateMap.has(r.date)) {
      dateMap.set(r.date, { date: r.date, followers: 0, total_posts: 0 });
    }
    const entry = dateMap.get(r.date)!;
    entry.followers = r.followers;
    entry.total_posts = r.published_content;
  });

  // Add snapshot data (overrides historical for same date)
  data.snapshots.forEach(r => {
    if (r.handle !== handle) return;
    if (!dateMap.has(r.date)) {
      dateMap.set(r.date, { date: r.date, followers: 0, total_posts: 0 });
    }
    const entry = dateMap.get(r.date)!;
    entry.followers = r.followers;
    entry.total_posts = r.total_posts;
  });

  return Array.from(dateMap.values()).sort((a, b) => a.date.localeCompare(b.date));
}