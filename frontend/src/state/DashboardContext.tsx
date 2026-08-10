import {
  createContext,
  type PropsWithChildren,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { api } from '../api/client';
import type {
  ChartView,
  CurrencyContext,
  Filters,
  Metadata,
  OrdersResponse,
  SortDirection,
  SortState,
  SummaryResponse,
} from '../types';

const defaultFilters: Filters = {
  dateFrom: '',
  dateTo: '',
  category: 'all',
  status: 'all',
  delayed: '',
  search: '',
};

type DashboardContextValue = {
  filters: Filters;
  sort: SortState;
  page: number;
  pageSize: number;
  chartView: ChartView;
  selectedOrderId: string | null;
  orders?: OrdersResponse;
  summary?: SummaryResponse;
  metadata?: Metadata;
  currencyContext?: CurrencyContext;
  ordersLoading: boolean;
  summaryLoading: boolean;
  metadataLoading: boolean;
  externalLoading: boolean;
  ingesting: boolean;
  ordersError?: string;
  summaryError?: string;
  metadataError?: string;
  externalError?: string;
  setFilter: <K extends keyof Filters>(key: K, value: Filters[K]) => void;
  resetFilters: () => void;
  setSort: (sortBy: string) => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  setChartView: (view: ChartView) => void;
  setSelectedOrderId: (orderId: string | null) => void;
  refresh: () => Promise<void>;
};

const DashboardContext = createContext<DashboardContextValue | null>(null);

export function DashboardProvider({ children }: PropsWithChildren) {
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [sort, setSortState] = useState<SortState>({ sortBy: 'order_date', sortDir: 'asc' });
  const [page, setPageState] = useState(1);
  const [pageSize, setPageSizeState] = useState(10);
  const [chartView, setChartView] = useState<ChartView>('revenue');
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const [orders, setOrders] = useState<OrdersResponse>();
  const [summary, setSummary] = useState<SummaryResponse>();
  const [metadata, setMetadata] = useState<Metadata>();
  const [currencyContext, setCurrencyContext] = useState<CurrencyContext>();

  const [ordersLoading, setOrdersLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [metadataLoading, setMetadataLoading] = useState(false);
  const [externalLoading, setExternalLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);

  const [ordersError, setOrdersError] = useState<string>();
  const [summaryError, setSummaryError] = useState<string>();
  const [metadataError, setMetadataError] = useState<string>();
  const [externalError, setExternalError] = useState<string>();

  const setFilter = useCallback(<K extends keyof Filters>(key: K, value: Filters[K]) => {
    setFilters((current) => ({ ...current, [key]: value }));
    setPageState(1);
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(defaultFilters);
    setPageState(1);
  }, []);

  const setSort = useCallback((sortBy: string) => {
    setSortState((current) => {
      const nextDirection: SortDirection =
        current.sortBy === sortBy && current.sortDir === 'asc' ? 'desc' : 'asc';
      return { sortBy, sortDir: nextDirection };
    });
  }, []);

  const setPage = useCallback((nextPage: number) => {
    setPageState(Math.max(1, nextPage));
  }, []);

  const setPageSize = useCallback((size: number) => {
    setPageSizeState(size);
    setPageState(1);
  }, []);

  const refresh = useCallback(async () => {
    setIngesting(true);
    setMetadataError(undefined);
    try {
      await api.ingestAll();
      setRefreshKey((key) => key + 1);
    } catch (error) {
      setMetadataError(error instanceof Error ? error.message : 'Unable to refresh data');
    } finally {
      setIngesting(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setMetadataLoading(true);
    setMetadataError(undefined);
    api
      .getMetadata(controller.signal)
      .then(setMetadata)
      .catch((error: Error) => {
        if (error.name !== 'AbortError') setMetadataError(error.message);
      })
      .finally(() => setMetadataLoading(false));
    return () => controller.abort();
  }, [refreshKey]);

  useEffect(() => {
    const controller = new AbortController();
    setOrdersLoading(true);
    setOrdersError(undefined);
    api
      .getOrders(filters, sort, page, pageSize, controller.signal)
      .then(setOrders)
      .catch((error: Error) => {
        if (error.name !== 'AbortError') setOrdersError(error.message);
      })
      .finally(() => setOrdersLoading(false));
    return () => controller.abort();
  }, [filters, sort, page, pageSize, refreshKey]);

  useEffect(() => {
    const controller = new AbortController();
    setSummaryLoading(true);
    setSummaryError(undefined);
    api
      .getSummary(filters, controller.signal)
      .then(setSummary)
      .catch((error: Error) => {
        if (error.name !== 'AbortError') setSummaryError(error.message);
      })
      .finally(() => setSummaryLoading(false));
    return () => controller.abort();
  }, [filters, refreshKey]);

  useEffect(() => {
    const controller = new AbortController();
    setExternalLoading(true);
    setExternalError(undefined);
    api
      .getCurrencyContext(controller.signal)
      .then(setCurrencyContext)
      .catch((error: Error) => {
        if (error.name !== 'AbortError') setExternalError(error.message);
      })
      .finally(() => setExternalLoading(false));
    return () => controller.abort();
  }, [refreshKey]);

  const value = useMemo<DashboardContextValue>(
    () => ({
      filters,
      sort,
      page,
      pageSize,
      chartView,
      selectedOrderId,
      orders,
      summary,
      metadata,
      currencyContext,
      ordersLoading,
      summaryLoading,
      metadataLoading,
      externalLoading,
      ingesting,
      ordersError,
      summaryError,
      metadataError,
      externalError,
      setFilter,
      resetFilters,
      setSort,
      setPage,
      setPageSize,
      setChartView,
      setSelectedOrderId,
      refresh,
    }),
    [
      filters,
      sort,
      page,
      pageSize,
      chartView,
      selectedOrderId,
      orders,
      summary,
      metadata,
      currencyContext,
      ordersLoading,
      summaryLoading,
      metadataLoading,
      externalLoading,
      ingesting,
      ordersError,
      summaryError,
      metadataError,
      externalError,
      setFilter,
      resetFilters,
      setSort,
      setPage,
      setPageSize,
      setSelectedOrderId,
      refresh,
    ],
  );

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>;
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used inside DashboardProvider');
  }
  return context;
}
