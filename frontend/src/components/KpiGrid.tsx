import { Clock3, IndianRupee, PackageCheck, TimerReset } from 'lucide-react';

import { useDashboard } from '../state/DashboardContext';
import { formatCurrency, formatNumber } from '../utils/format';
import { StatusMessage } from './StatusMessage';

export function KpiGrid() {
  const { summary, summaryLoading, summaryError } = useDashboard();

  if (summaryLoading && !summary) {
    return <StatusMessage state="loading" title="Loading KPIs" />;
  }
  if (summaryError) {
    return <StatusMessage state="error" title="Unable to load KPIs" detail={summaryError} />;
  }
  if (!summary) {
    return <StatusMessage state="empty" title="No KPI data available" />;
  }

  const { kpis, currency } = summary;

  return (
    <section className="kpi-grid" aria-label="Key metrics">
      <article className="kpi-card blue">
        <PackageCheck size={22} aria-hidden="true" />
        <span>Total orders</span>
        <strong>{formatNumber(kpis.total_orders)}</strong>
        <small>{formatNumber(kpis.total_items)} items sold</small>
      </article>
      <article className="kpi-card green">
        <IndianRupee size={22} aria-hidden="true" />
        <span>Total revenue</span>
        <strong>{formatCurrency(kpis.total_revenue, currency.base_currency)}</strong>
        <small>
          {formatCurrency(kpis.converted_total_revenue, currency.display_currency)} converted
        </small>
      </article>
      <article className="kpi-card red">
        <TimerReset size={22} aria-hidden="true" />
        <span>Delayed orders</span>
        <strong>{formatNumber(kpis.delayed_orders)}</strong>
        <small>{formatNumber(kpis.on_time_orders)} on time</small>
      </article>
      <article className="kpi-card amber">
        <Clock3 size={22} aria-hidden="true" />
        <span>Avg delivery</span>
        <strong>{kpis.average_delivery_days ?? '-'} days</strong>
        <small>Across filtered orders</small>
      </article>
    </section>
  );
}
