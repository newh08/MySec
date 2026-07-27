const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ScheduleItem {
  id: number;
  log_id: number;
  title: string;
  start_time: string;
  end_time: string;
  location: string | null;
  description: string | null;
  is_synced_to_calendar: boolean;
}

export interface LogSummary {
  id: number;
  date: string;
  summary_markdown: string;
  schedules: ScheduleItem[];
  created_at: string;
}

export interface LogDetail extends LogSummary {
  raw_conversation_json: string | null;
}

export interface LogsResponse {
  items: LogSummary[];
  total: number;
  page: number;
  limit: number;
}

export async function fetchLogs(
  page = 1,
  limit = 20,
  startDate?: string,
  endDate?: string
): Promise<LogsResponse> {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) });
  if (startDate) params.set("start_date", startDate);
  if (endDate) params.set("end_date", endDate);

  const res = await fetch(`${API_URL}/api/logs?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch logs: ${res.status}`);
  return res.json();
}

export async function fetchLogDetail(logId: number): Promise<LogDetail> {
  const res = await fetch(`${API_URL}/api/logs/${logId}`);
  if (!res.ok) throw new Error(`Failed to fetch log ${logId}: ${res.status}`);
  return res.json();
}

export async function fetchSchedules(
  startDate?: string,
  endDate?: string
): Promise<ScheduleItem[]> {
  const params = new URLSearchParams();
  if (startDate) params.set("start_date", startDate);
  if (endDate) params.set("end_date", endDate);

  const res = await fetch(`${API_URL}/api/schedules?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch schedules: ${res.status}`);
  return res.json();
}

export async function deleteLog(logId: number): Promise<void> {
  const res = await fetch(`${API_URL}/api/logs/${logId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to delete log ${logId}: ${res.status}`);
}
