import { RotateCcw, Search } from 'lucide-react';

import { useDashboard } from '../state/DashboardContext';

export function FilterBar() {
  const { filters, metadata, metadataLoading, metadataError, setFilter, resetFilters } = useDashboard();

  return (
    <section className="filter-band" aria-label="Filters">
      <label>
        <span>Search</span>
        <div className="input-with-icon">
          <Search size={16} aria-hidden="true" />
          <input
            type="search"
            value={filters.search}
            onChange={(event) => setFilter('search', event.target.value)}
            placeholder="Order, customer, product"
          />
        </div>
      </label>

      <label>
        <span>Date from</span>
        <input
          type="date"
          value={filters.dateFrom}
          onChange={(event) => setFilter('dateFrom', event.target.value)}
        />
      </label>

      <label>
        <span>Date to</span>
        <input
          type="date"
          value={filters.dateTo}
          onChange={(event) => setFilter('dateTo', event.target.value)}
        />
      </label>

      <label>
        <span>Category</span>
        <select
          value={filters.category}
          disabled={metadataLoading || Boolean(metadataError)}
          onChange={(event) => setFilter('category', event.target.value)}
        >
          <option value="all">All categories</option>
          {(metadata?.categories ?? []).map((category) => (
            <option value={category} key={category}>
              {category}
            </option>
          ))}
        </select>
      </label>

      <label>
        <span>Status</span>
        <select
          value={filters.status}
          disabled={metadataLoading || Boolean(metadataError)}
          onChange={(event) => setFilter('status', event.target.value)}
        >
          <option value="all">All statuses</option>
          {(metadata?.shipment_statuses ?? []).map((status) => (
            <option value={status} key={status}>
              {status}
            </option>
          ))}
        </select>
      </label>

      <label>
        <span>Delivery</span>
        <select
          value={filters.delayed}
          onChange={(event) => setFilter('delayed', event.target.value as '' | 'true' | 'false')}
        >
          <option value="">All deliveries</option>
          <option value="false">On time</option>
          <option value="true">Delayed</option>
        </select>
      </label>

      <button className="ghost-button" type="button" onClick={resetFilters}>
        <RotateCcw size={16} aria-hidden="true" />
        Reset
      </button>
    </section>
  );
}
