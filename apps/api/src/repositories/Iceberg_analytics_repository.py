class AnalyticsRepository:
    def __init__(self, db):
        self.supabase = db

    def summary(self):
        result = (
            self.supabase
            .table("analytics_summary")
            .select("*")
            .eq("id", 1)
            .single()
            .execute()
        )
        return result.data

    def by_state(self):
        result = (
            self.supabase
            .table("analytics_by_state")
            .select("*")
            .order("total_opportunities", desc=True)
            .execute()
        )
        return result.data