import { BarChart3, PackageSearch, RefreshCw } from 'lucide-react';

import { DashboardProvider, useDashboard } from './state/DashboardContext';
import { ExternalContext } from './components/ExternalContext';
import { FilterBar } from './components/FilterBar';
import { KpiGrid } from './components/KpiGrid';
import { OrdersTable } from './components/OrdersTable';
import { SummaryCharts } from './components/SummaryCharts';

function Dashboard() {
  const { refresh, ingesting } = useDashboard();

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Dashboard navigation">
        <div className="brand">
          <div className="brand-mark">
            <PackageSearch size={22} />
          </div>
          <div>
            <strong>OrderOps</strong>
            <span>Assessment</span>
          </div>
        </div>
        <nav>
          <a className="nav-item active" href="#dashboard">
            <BarChart3 size={18} />
            Dashboard
          </a>
        </nav>
      </aside>

      <main className="main-content" id="dashboard">
        <header className="topbar">
          <div>
            <p className="eyebrow">Operations dashboard</p>
            <h1>Orders, revenue, and delivery performance</h1>
          </div>
          <button className="primary-button" type="button" onClick={refresh} disabled={ingesting}>
            <RefreshCw size={18} aria-hidden="true" />
            {ingesting ? 'Refreshing' : 'Refresh data'}
          </button>
        </header>

        <FilterBar />
        <KpiGrid />
        <SummaryCharts />
        <OrdersTable />
        <ExternalContext />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <DashboardProvider>
      <Dashboard />
    </DashboardProvider>
  );
}
