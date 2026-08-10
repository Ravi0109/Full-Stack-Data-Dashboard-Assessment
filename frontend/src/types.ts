export type SortDirection = 'asc' | 'desc';

export type Filters = {
  dateFrom: string;
  dateTo: string;
  category: string;
  status: string;
  delayed: '' | 'true' | 'false';
  search: string;
};

export type SortState = {
  sortBy: string;
  sortDir: SortDirection;
};

export type OrderItem = {
  product_id: string;
  product_name: string;
  category: string;
  quantity: number;
  unit_price: number;
  line_total: number;
};

export type Order = {
  order_id: string;
  customer_id: string;
  customer_name: string;
  order_date: string;
  items: OrderItem[];
  item_count: number;
  categories: string[];
  total_value: number;
  base_currency: string;
  converted_total_value: number;
  display_currency: string;
  shipment_status: string;
  delivery_days: number | null;
  is_delayed: boolean;
};

export type Pagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
};

export type CurrencyInfo = {
  base_currency: string;
  display_currency: string;
  rate: number;
  status: string;
  source: string;
  updated_at: string;
  error?: string;
};

export type OrdersResponse = {
  data: Order[];
  pagination: Pagination;
  sort: {
    sort_by: string;
    sort_dir: SortDirection;
  };
  filters: Record<string, string | boolean | null>;
  currency: CurrencyInfo;
};

export type SummaryResponse = {
  kpis: {
    total_orders: number;
    total_revenue: number;
    converted_total_revenue: number;
    delayed_orders: number;
    on_time_orders: number;
    total_items: number;
    average_delivery_days: number | null;
  };
  category_revenue: Array<{
    category: string;
    revenue: number;
    quantity: number;
    order_count: number;
  }>;
  revenue_trend: Array<{
    date: string;
    revenue: number;
    order_count: number;
  }>;
  delivery_performance: Array<{
    status: string;
    count: number;
  }>;
  currency: CurrencyInfo;
  currency_context: CurrencyContext;
};

export type Metadata = {
  categories: string[];
  shipment_statuses: string[];
  loaded_at: string | null;
  source_counts: {
    orders: number;
    products: number;
    shipments: number;
    normalized_orders: number;
  };
  errors: string[];
  allowed_sort_fields?: string[];
};

export type CurrencyContext = {
  currency: string;
  status: string;
  source: string;
  countries_using_currency: number;
  updated_at: string;
  error?: string;
  top_countries: Array<{
    name: string;
    code: string;
    region: string;
    population: number;
    area: number;
    population_density: number | null;
  }>;
};

export type ChartView = 'revenue' | 'orders';
