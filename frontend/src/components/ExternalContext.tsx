import { useEffect, useMemo, useState } from 'react';
import { ArrowUpDown, ChevronLeft, ChevronRight, Globe2, SlidersHorizontal } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { api } from '../api/client';
import { useDashboard } from '../state/DashboardContext';
import type {
  ExternalRelationshipFilters,
  ExternalRelationshipRow,
  ExternalRelationshipsResponse,
  SortDirection,
  SortState,
} from '../types';
import { formatNumber } from '../utils/format';
import { StatusMessage } from './StatusMessage';

const defaultFilters: ExternalRelationshipFilters = {
  region: 'all',
  populationMin: '',
  populationMax: '',
};

const columns = [
  { key: 'country', label: 'Country' },
  { key: 'region', label: 'Region' },
  { key: 'currency_code', label: 'Currency' },
  { key: 'population', label: 'Population' },
  { key: 'population_density', label: 'Density' },
];

export function ExternalContext() {
  const { currencyContext, externalLoading, externalError } = useDashboard();
  const [filters, setFilters] = useState<ExternalRelationshipFilters>(defaultFilters);
  const [sort, setSort] = useState<SortState>({
    sortBy: 'population_density',
    sortDir: 'desc',
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [relationships, setRelationships] = useState<ExternalRelationshipsResponse>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setError(undefined);
    api
      .getCountryCurrencyPopulation(filters, sort, page, pageSize, controller.signal)
      .then((payload) => {
        if (active) setRelationships(payload);
      })
      .catch((requestError: Error) => {
        if (active && requestError.name !== 'AbortError') setError(requestError.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [filters, page, pageSize, sort]);

  const densityData = useMemo(
    () => relationships?.density_comparison ?? [],
    [relationships],
  );

  const updateFilter = <K extends keyof ExternalRelationshipFilters>(
    key: K,
    value: ExternalRelationshipFilters[K],
  ) => {
    setFilters((current) => ({ ...current, [key]: value }));
    setPage(1);
  };

  const toggleSort = (sortBy: string) => {
    setSort((current) => {
      const sortDir: SortDirection =
        current.sortBy === sortBy && current.sortDir === 'asc' ? 'desc' : 'asc';
      return { sortBy, sortDir };
    });
    setPage(1);
  };

  return (
    <section className="external-panel" aria-label="External country currency population dashboard">
      <div className="panel-heading">
        <div>
          <h2>External API Relationships</h2>
          <span>Country -&gt; currency -&gt; population from REST Countries</span>
        </div>
        <Globe2 size={22} aria-hidden="true" />
      </div>

      {currencyContext ? (
        <div className="external-summary relationship-summary">
          <strong>{currencyContext.currency}</strong>
          <span>
            {currencyContext.status === 'ok'
              ? `${formatNumber(currencyContext.countries_using_currency)} countries use source currency`
              : 'Source currency lookup is using fallback data'}
          </span>
        </div>
      ) : externalLoading ? (
        <StatusMessage state="loading" title="Loading source currency snapshot" />
      ) : externalError ? (
        <StatusMessage state="empty" title="Source currency snapshot unavailable" detail={externalError} />
      ) : null}

      <div className="external-filter-grid">
        <label>
          <span>Region</span>
          <select value={filters.region} onChange={(event) => updateFilter('region', event.target.value)}>
            <option value="all">All regions</option>
            {(relationships?.regions ?? []).map((region) => (
              <option value={region} key={region}>
                {region}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Population min</span>
          <input
            type="number"
            min={0}
            value={filters.populationMin}
            onChange={(event) => updateFilter('populationMin', event.target.value)}
            placeholder="0"
          />
        </label>
        <label>
          <span>Population max</span>
          <input
            type="number"
            min={0}
            value={filters.populationMax}
            onChange={(event) => updateFilter('populationMax', event.target.value)}
            placeholder="1500000000"
          />
        </label>
        <label>
          <span>Rows</span>
          <select
            value={pageSize}
            onChange={(event) => {
              setPageSize(Number(event.target.value));
              setPage(1);
            }}
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
        </label>
        <button
          className="ghost-button"
          type="button"
          onClick={() => {
            setFilters(defaultFilters);
            setPage(1);
          }}
        >
          <SlidersHorizontal size={16} aria-hidden="true" />
          Reset
        </button>
      </div>

      {error ? (
        <StatusMessage state="error" title="Unable to load external relationships" detail={error} />
      ) : loading && !relationships ? (
        <StatusMessage state="loading" title="Loading external relationships" />
      ) : !relationships ? (
        <StatusMessage state="empty" title="No external relationship data available" />
      ) : relationships.status === 'fallback' ? (
        <StatusMessage
          state="empty"
          title="External relationship data is temporarily unavailable"
          detail={relationships.error}
        />
      ) : (
        <>
          <MetricGrid relationships={relationships} />
          <div className="relationship-layout">
            <DensityPanel densityData={densityData} />
            <RelationshipTable
              relationships={relationships}
              sort={sort}
              page={page}
              onSort={toggleSort}
              onPageChange={setPage}
            />
          </div>
        </>
      )}
    </section>
  );
}

function MetricGrid({ relationships }: { relationships: ExternalRelationshipsResponse }) {
  const { metrics } = relationships;
  return (
    <div className="external-metric-grid">
      <Metric label="Relationships" value={formatNumber(metrics.relationship_count)} />
      <Metric label="Countries" value={formatNumber(metrics.country_count)} />
      <Metric label="Currencies" value={formatNumber(metrics.currency_count)} />
      <Metric label="Avg density" value={formatDensity(metrics.average_population_density)} />
    </div>
  );
}

function DensityPanel({
  densityData,
}: {
  densityData: ExternalRelationshipsResponse['density_comparison'];
}) {
  return (
    <div className="density-panel">
      <div className="panel-heading">
        <div>
          <h2>Density Proxy</h2>
          <span>Highest population density by filtered countries</span>
        </div>
      </div>
      {densityData.length ? (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={densityData} layout="vertical" margin={{ top: 8, right: 18, left: 20, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis dataKey="country" type="category" width={92} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value) => formatDensity(Number(value))} />
            <Bar dataKey="population_density" fill="#0f766e" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <StatusMessage state="empty" title="No density values for the selected filters" />
      )}
    </div>
  );
}

type RelationshipTableProps = {
  relationships: ExternalRelationshipsResponse;
  sort: SortState;
  page: number;
  onSort: (sortBy: string) => void;
  onPageChange: (page: number) => void;
};

function RelationshipTable({
  relationships,
  sort,
  page,
  onSort,
  onPageChange,
}: RelationshipTableProps) {
  const { pagination } = relationships;
  return (
    <div className="relationship-table-wrap">
      <div className="panel-heading">
        <div>
          <h2>Normalized Rows</h2>
          <span>{formatNumber(pagination.total)} country-currency rows after filters</span>
        </div>
      </div>
      {relationships.data.length ? (
        <>
          <div className="table-scroll">
            <table className="relationship-table">
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column.key}>
                      <button
                        type="button"
                        className={sort.sortBy === column.key ? 'sort-button active' : 'sort-button'}
                        onClick={() => onSort(column.key)}
                        title={`Sort by ${column.label}`}
                      >
                        {column.label}
                        <ArrowUpDown size={14} aria-hidden="true" />
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {relationships.data.map((row) => (
                  <RelationshipRow key={`${row.country_code}-${row.currency_code}`} row={row} />
                ))}
              </tbody>
            </table>
          </div>
          <footer className="pagination-bar">
            <span>
              Page {pagination.page} of {pagination.total_pages}
            </span>
            <div>
              <button
                className="icon-button"
                type="button"
                title="Previous relationship page"
                disabled={!pagination.has_previous}
                onClick={() => onPageChange(page - 1)}
              >
                <ChevronLeft size={18} aria-hidden="true" />
              </button>
              <button
                className="icon-button"
                type="button"
                title="Next relationship page"
                disabled={!pagination.has_next}
                onClick={() => onPageChange(page + 1)}
              >
                <ChevronRight size={18} aria-hidden="true" />
              </button>
            </div>
          </footer>
        </>
      ) : (
        <StatusMessage state="empty" title="No rows match the selected filters" />
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="external-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RelationshipRow({ row }: { row: ExternalRelationshipRow }) {
  return (
    <tr>
      <td>
        <strong>{row.country}</strong>
        <small>{row.country_code}</small>
      </td>
      <td>{row.region}</td>
      <td>
        <strong>{row.currency_code}</strong>
        <small>
          {row.currency_name}
          {row.currency_symbol ? ` (${row.currency_symbol})` : ''}
        </small>
      </td>
      <td>{formatNumber(row.population)}</td>
      <td>{formatDensity(row.population_density)}</td>
    </tr>
  );
}

function formatDensity(value: number | null) {
  return value === null ? '-' : `${formatNumber(value)}/sq km`;
}
