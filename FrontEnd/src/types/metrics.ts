/** Monetary values arrive as strings from FastAPI's Decimal fields. */
export interface WeeklyMetric {
  week_start: string;
  gross_purchase_spending: string;
  refund_amount: string;
  net_observed_spending: string;
  purchase_count: number;
  unique_purchasing_customers: number;
  average_purchase_amount: string | null;
}