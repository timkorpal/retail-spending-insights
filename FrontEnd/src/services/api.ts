import type { WeeklyMetric } from "../types/metrics";

const API_URL = "http://127.0.0.1:8000";

/** Retrieve available merchants. */
export async function getMerchants(
  signal?: AbortSignal,
): Promise<string[]> {
  const response = await fetch(`${API_URL}/merchants`, { signal });

  if (!response.ok) {
    throw new Error(`Unable to load merchants (${response.status}).`);
  }

  return response.json();
}

/** Retrieve all available weekly metrics for one merchant. */
export async function getWeeklyMetrics(
  merchant: string,
  signal?: AbortSignal,
): Promise<WeeklyMetric[]> {
  // Encoding safely handles spaces and other characters in merchant names.
  const merchantPath = encodeURIComponent(merchant);

  const response = await fetch(
    `${API_URL}/merchants/${merchantPath}/weekly-metrics`,
    { signal },
  );

  if (!response.ok) {
    throw new Error(`Unable to load weekly metrics (${response.status}).`);
  }

  return response.json();
}