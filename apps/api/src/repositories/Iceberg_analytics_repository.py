from typing import Any, cast

from supabase import Client


class AnalyticsRepository:
    def __init__(self, db: Client) -> None:
        self.supabase = db

    def summary(self) -> dict[str, Any] | None:
        result = (
            self.supabase.table("analytics_summary")
            .select("*")
            .eq("id", 1)
            .single()
            .execute()
        )
        return cast(dict[str, Any] | None, result.data)

    def by_state(self) -> list[dict[str, Any]]:
        result = (
            self.supabase.table("analytics_by_state")
            .select("*")
            .order("total_opportunities", desc=True)
            .execute()
        )
        return result.data or []
