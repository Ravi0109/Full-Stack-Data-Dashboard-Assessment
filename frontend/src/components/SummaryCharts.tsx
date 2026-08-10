import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { useDashboard } from '../state/DashboardContext';
import { StatusMessage } from './StatusMessage';

const DELIVERY_COLORS = ['#16a34a', '#dc2626', '#64748b'];

export function SummaryCharts() {
  const { summary, summaryLoading, summaryError, chartView, setChartView } = useDashboard();

  if (summaryLoading && !summary) {
    return <StatusMessage state="loading" title="Loading charts" />;
  }
  if (summaryError) {
    return <StatusMessage state="error" title="Unable to load charts" detail={summaryError} />;
  }
  if (!summary) {
    return <StatusMessage state="empty" title="No chart data available" />;
  }

  const trendKey = chartView === 'revenue' ? 'revenue' : 'order_count';

  return (
    <section className="chart-grid" aria-label="Analytics charts">
      <article className="chart-panel wide">
        <div className="panel-heading">
          <div>
            <h2>Trend</h2>
            <span>Daily revenue and order volume</span>
          </div>
          <div className="segmented-control" aria-label="Chart view">
            <button
              type="button"
              className={chartView === 'revenue' ? 'active' : ''}
              onClick={() => setChartView('revenue')}
            >
              Revenue
            </button>
            <button
              type="button"
              className={chartView === 'orders' ? 'active' : ''}
              onClick={() => setChartView('orders')}
            >
              Orders
            </button>
          </div>
        </div>
        {summary.revenue_trend.length ? (
          <ResponsiveContainer width="100%" height={270}>
            <LineChart data={summary.revenue_trend} margin={{ top: 12, right: 18, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey={trendKey}
                stroke="#2563eb"
                strokeWidth={3}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <StatusMessage state="empty" title="No trend data for the selected filters" />
        )}
      </article>

      <article className="chart-panel">
        <div className="panel-heading">
          <div>
            <h2>Category Revenue</h2>
            <span>Revenue by product category</span>
          </div>
        </div>
        {summary.category_revenue.length ? (
          <ResponsiveContainer width="100%" height={270}>
            <BarChart data={summary.category_revenue} margin={{ top: 12, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="category" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="revenue" fill="#0f766e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <StatusMessage state="empty" title="No category data for the selected filters" />
        )}
      </article>

      <article className="chart-panel">
        <div className="panel-heading">
          <div>
            <h2>Delivery Performance</h2>
            <span>Delayed versus on-time orders</span>
          </div>
        </div>
        {summary.delivery_performance.length ? (
          <ResponsiveContainer width="100%" height={270}>
            <PieChart>
              <Pie
                data={summary.delivery_performance}
                dataKey="count"
                nameKey="status"
                innerRadius={52}
                outerRadius={92}
                paddingAngle={2}
              >
                {summary.delivery_performance.map((entry, index) => (
                  <Cell key={entry.status} fill={DELIVERY_COLORS[index % DELIVERY_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <StatusMessage state="empty" title="No delivery data for the selected filters" />
        )}
      </article>
    </section>
  );
}
