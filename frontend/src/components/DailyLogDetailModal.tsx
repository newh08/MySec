"use client";

import { useEffect, useState } from "react";
import { Calendar, MapPin, X, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { LogDetail } from "@/lib/api";
import { fetchLogDetail } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

interface Props {
  logId: number | null;
  onClose: () => void;
}

export default function DailyLogDetailModal({ logId, onClose }: Props) {
  const [log, setLog] = useState<LogDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!logId) return;
    setLoading(true);
    fetchLogDetail(logId)
      .then(setLog)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [logId]);

  if (!logId) return null;

  const dateObj = log ? new Date(log.date + "T00:00:00") : null;
  const formatted = dateObj
    ? `${dateObj.getFullYear()}년 ${dateObj.getMonth() + 1}월 ${dateObj.getDate()}일`
    : "";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <Card className="relative w-full max-w-2xl max-h-[85vh] flex flex-col">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="text-lg">{formatted} 회고</CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <Separator />
        <ScrollArea className="flex-1 p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : log ? (
            <div className="space-y-6">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {log.summary_markdown}
                </ReactMarkdown>
              </div>

              {log.schedules.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold mb-3">📅 일정</h3>
                  <div className="space-y-2">
                    {log.schedules.map((s) => (
                      <Card key={s.id} className="p-3">
                        <div className="flex items-start justify-between">
                          <div className="space-y-1">
                            <p className="font-medium text-sm">{s.title}</p>
                            <div className="flex items-center gap-3 text-xs text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                {new Date(s.start_time).toLocaleString("ko-KR")}
                                {" ~ "}
                                {new Date(s.end_time).toLocaleString("ko-KR")}
                              </span>
                              {s.location && (
                                <span className="flex items-center gap-1">
                                  <MapPin className="h-3 w-3" />
                                  {s.location}
                                </span>
                              )}
                            </div>
                            {s.description && (
                              <p className="text-xs text-muted-foreground mt-1">
                                {s.description}
                              </p>
                            )}
                          </div>
                          {s.is_synced_to_calendar && (
                            <Badge variant="outline" className="shrink-0">
                              Google
                            </Badge>
                          )}
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {log.raw_conversation_json && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">💬 원본 대화</h3>
                  <div className="bg-muted rounded-lg p-4 text-xs font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
                    {(() => {
                      try {
                        const raw = JSON.parse(log.raw_conversation_json);
                        return raw.conversation_history
                          ?.map(
                            (m: { role: string; content: string }) =>
                              `[${m.role === "assistant" ? "AI" : "나"}] ${m.content}`
                          )
                          .join("\n") || log.raw_conversation_json;
                      } catch {
                        return log.raw_conversation_json;
                      }
                    })()}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              데이터를 불러올 수 없습니다.
            </p>
          )}
        </ScrollArea>
      </Card>
    </div>
  );
}
