import { useEffect, useState } from "react";

import { getMerchants, getWeeklyMetrics } from "./services/api";
import type { WeeklyMetric } from "./types/metrics";

import "./App.css";


const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

const countFormatter = new Intl.NumberFormat("en-US");


/** Convert a decimal string to a number for display only. */
function formatMoney(value: string | null): string {
  return value === null
    ? "—"
    : currencyFormatter.format(Number(value));
}


/** Display a date without shifting it through the browser's timezone. */
function formatDate(value: string): string {
  const [year, month, day] = value.split("-");
  return `${month}/${day}/${year}`;
}


function App() {
  const [merchants, setMerchants] = useState<string[]>([]);
  const [selectedMerchant, setSelectedMerchant] = useState("");

  const [metrics, setMetrics] = useState<WeeklyMetric[]>([]);

  const [loadingMerchants, setLoadingMerchants] = useState(true);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  const [merchantError, setMerchantError] = useState("");
  const [metricsError, setMetricsError] = useState("");


  // Load merchants when the component mounts.
  useEffect(() => {
    const controller = new AbortController();

    async function loadMerchants() {
      try {
        const data = await getMerchants(controller.signal);

        if (controller.signal.aborted) return;

        setMerchants(data);
        setSelectedMerchant(data[0] ?? "");

      } catch (error: unknown) {
        if (controller.signal.aborted) return;

        setMerchantError(
          error instanceof Error
            ? error.message
            : "An unexpected error occurred.",
        );

      } finally {
        if (!controller.signal.aborted) {
          setLoadingMerchants(false);
        }
      }
    }

    void loadMerchants();

    // Cancel the request when the component unmounts.
    return () => controller.abort();
  }, []);


  // Load metrics whenever the selected merchant changes.
  useEffect(() => {
    if (!selectedMerchant) return;

    const controller = new AbortController();

    async function loadMetrics() {
      setLoadingMetrics(true);
      setMetricsError("");
      setMetrics([]);

      try {
        const data = await getWeeklyMetrics(
          selectedMerchant,
          controller.signal,
        );

        if (controller.signal.aborted) return;

        setMetrics(data);

      } catch (error: unknown) {
        if (controller.signal.aborted) return;

        setMetricsError(
          error instanceof Error
            ? error.message
            : "An unexpected error occurred.",
        );

      } finally {
        if (!controller.signal.aborted) {
          setLoadingMetrics(false);
        }
      }
    }

    void loadMetrics();

    // Cancel the previous request if the user changes merchants.
    // This prevents an older response from replacing newer results.
    return () => controller.abort();
  }, [selectedMerchant]);


  function handleMerchantChange(merchant: string) {
    // Clear the previous merchant's results immediately.
    setMetrics([]);
    setMetricsError("");
    setLoadingMetrics(true);
    setSelectedMerchant(merchant);
  }


  return (
    <main className="dashboard">
      <header>
        <h1>Retail Spending Insights</h1>

        <p className="description">
          Weekly spending trends from synthetic transaction data.
        </p>
      </header>

      <section className="controls" aria-label="Merchant selection">
        <label htmlFor="merchant">Merchant</label>

        <select
          id="merchant"
          value={selectedMerchant}
          disabled={loadingMerchants || merchants.length === 0}
          onChange={(event) =>
            handleMerchantChange(event.target.value)
          }
        >
          {merchants.length === 0 && (
            <option value="">No merchants available</option>
          )}

          {merchants.map((merchant) => (
            <option key={merchant} value={merchant}>
              {merchant}
            </option>
          ))}
        </select>
      </section>

      <div role="status" aria-live="polite">
        {loadingMerchants && <p>Loading merchants...</p>}
        {loadingMetrics && <p>Loading weekly metrics...</p>}

        {!loadingMerchants && !merchantError &&
          merchants.length === 0 && (
            <p>Import transaction data to see available merchants.</p>
          )}
      </div>

      {merchantError && (
        <p className="error" role="alert">{merchantError}</p>
      )}

      {metricsError && (
        <p className="error" role="alert">{metricsError}</p>
      )}

      {!loadingMetrics && !metricsError && metrics.length > 0 && (
        <section aria-labelledby="metrics-heading">
          <h2 id="metrics-heading">
            {selectedMerchant}: Weekly metrics
          </h2>

          <div className="table-container">
            <table>
              <caption>
                Weeks begin Monday. Boundary weeks may be partial,
                and source completeness has not been verified.
              </caption>

              <thead>
                <tr>
                  <th scope="col">Week starting</th>
                  <th scope="col">Gross spending</th>
                  <th scope="col">Refunds</th>
                  <th scope="col">Net spending</th>
                  <th scope="col">Purchases</th>
                  <th scope="col">Unique customers</th>
                  <th scope="col">Average purchase</th>
                </tr>
              </thead>

              <tbody>
                {metrics.map((metric) => (
                  <tr key={metric.week_start}>
                    <th scope="row">
                      {formatDate(metric.week_start)}
                    </th>

                    <td>
                      {formatMoney(metric.gross_purchase_spending)}
                    </td>

                    <td>{formatMoney(metric.refund_amount)}</td>

                    <td>
                      {formatMoney(metric.net_observed_spending)}
                    </td>

                    <td>
                      {countFormatter.format(metric.purchase_count)}
                    </td>

                    <td>
                      {countFormatter.format(
                        metric.unique_purchasing_customers,
                      )}
                    </td>

                    <td>
                      {formatMoney(metric.average_purchase_amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {selectedMerchant && !loadingMetrics &&
        !metricsError && metrics.length === 0 && (
          <p>No weekly metrics available for this merchant.</p>
        )}

      <p className="data-note">
        Synthetic sample data. Observed spending does not represent
        total company revenue.
      </p>
    </main>
  );
}

export default App;