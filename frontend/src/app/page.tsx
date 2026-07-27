"use client";

import { useEffect, useState, useCallback } from "react";
import { Loader2, BookOpen, CalendarDays } from "lucide-react";

import type { LogSummary } from "@/lib/api";
import { fetchLogs } from "@/lib/api";
import DailyLogCard from "@/components/DailyLogCard";
import DailyLogDetailModal from "@/components/DailyLogDetailModal";
import ThemeToggle from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

export default function Home() {
  const [logs, setLogs] = useState<LogSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [selectedLogId, setSelectedLogId] = useState<number | null>(null);

  const loadLogs = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const data = await fetchLogs(p, 20);
      if (p === 1) {
        setLogs(data.items);
      } else {
        setLogs((prev) => [...prev, ...data.items]);
      }
      setHasMore(data.items.length === 20);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLogs(1);
  }, [loadLogs]);

  const loadMore = () => {
    const next = page + 1;
    setPage(next);
    loadLogs(next);
  };

  const today = new Date();
  const dateStr = `${today.getFullYear()}년 ${today.getMonth() + 1}월 ${today.getDate()}일`;

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
        <div className="max-w-4xl mx-auto flex items-center justify-between px-4 h-14">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <h1 className="text-lg font-semibold">MySecretary</h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground hidden sm:inline">
              {dateStr}
            </span>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold tracking-tight">📖 회고 타임라인</h2>
          <p className="text-sm text-muted-foreground mt-1">
            매일 밤 디스코드로 기록된 하루 회고를 확인하세요.
          </p>
        </div>

        {logs.length === 0 && !loading && (
          <div className="text-center py-20">
            <CalendarDays className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground">아직 기록된 회고가 없습니다.</p>
            <p className="text-xs text-muted-foreground/60 mt-1">
              밤 11시 디스코드 알림을 기다려 주세요.
            </p>
          </div>
        )}

        <div className="space-y-4">
          {logs.map((log) => (
            <DailyLogCard
              key={log.id}
              log={log}
              onClick={() => setSelectedLogId(log.id)}
            />
          ))}
        </div>

        {hasMore && logs.length > 0 && (
          <div className="flex justify-center mt-8">
            <Button variant="outline" onClick={loadMore} disabled={loading}>
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : null}
              더 보기
            </Button>
          </div>
        )}

        {loading && logs.length === 0 && (
          <div className="flex justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}
      </main>

      <Separator />

      <footer className="py-6 text-center text-xs text-muted-foreground">
        MySecretary · Personal AI Secretary
      </footer>

      <DailyLogDetailModal
        logId={selectedLogId}
        onClose={() => setSelectedLogId(null)}
      />
    </div>
  );
}
