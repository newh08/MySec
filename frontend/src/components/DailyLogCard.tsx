"use client";

import { Calendar, MapPin } from "lucide-react";

import type { LogSummary } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

interface Props {
  log: LogSummary;
  onClick: () => void;
}

export default function DailyLogCard({ log, onClick }: Props) {
  const dateObj = new Date(log.date + "T00:00:00");
  const dayNames = ["일", "월", "화", "수", "목", "금", "토"];
  const formatted = `${dateObj.getFullYear()}년 ${dateObj.getMonth() + 1}월 ${dateObj.getDate()}일 (${dayNames[dateObj.getDay()]})`;

  return (
    <Card
      className="cursor-pointer transition-all hover:shadow-lg hover:border-primary/50"
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <time className="text-sm font-medium text-muted-foreground">
            {formatted}
          </time>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="prose prose-sm dark:prose-invert line-clamp-4 max-w-none">
          <PreviewMarkdown content={log.summary_markdown} />
        </div>
        {log.schedules.length > 0 && (
          <div className="space-y-1.5 pt-2 border-t">
            {log.schedules.map((s) => (
              <div key={s.id} className="flex items-center gap-2 text-xs">
                <Calendar className="h-3 w-3 shrink-0 text-blue-500" />
                <span className="font-medium truncate">{s.title}</span>
                {s.location && (
                  <>
                    <MapPin className="h-3 w-3 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground truncate">
                      {s.location}
                    </span>
                  </>
                )}
                {s.is_synced_to_calendar && (
                  <Badge variant="outline" className="ml-auto shrink-0 text-[10px] px-1.5 py-0">
                    Google
                  </Badge>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PreviewMarkdown({ content }: { content: string }) {
  const lines = content.split("\n").filter(Boolean);
  const preview = lines.slice(0, 6).join("\n");
  return (
    <div className="whitespace-pre-line">{preview}</div>
  );
}
