import { ArrowUpDown, ChevronDown, ChevronLeft, ChevronRight, ChevronUp } from 'lucide-react';

import { useDashboard } from '../state/DashboardContext';
import type { Order } from '../types';
import { formatCurrency, formatDate, formatNumber } from '../utils/format';
import { StatusMessage } from './StatusMessage';

const columns = [
  { key: 'order_id', label: 'Order' },
  { key: 'customer_name', label: 'Customer' },
  { key: 'order_date', label: 'Date' },
  { key: 'total_value', label: 'Revenue' },
  { key: 'shipment_status', label: 'Status' },
  { key: 'delivery_days', label: 'Days' },
];

export function OrdersTable() {
  const {
    orders,
    ordersLoading,
    ordersError,
    sort,
    page,
    pageSize,
    selectedOrderId,
    setSort,
    setPage,
    setPageSize,
    setSelectedOrderId,
  } = useDashboard();

  if (ordersLoading && !orders) {
    return <StatusMessage state="loading" title="Loading orders" />;
  }
  if (ordersError) {
    return <StatusMessage state="error" title="Unable to load orders" detail={ordersError} />;
  }
  if (!orders || orders.data.length === 0) {
    return <StatusMessage state="empty" title="No orders match the selected filters" />;
  }

  return (
    <section className="table-panel" aria-label="Orders table">
      <div className="panel-heading table-heading">
        <div>
          <h2>Orders</h2>
          <span>{formatNumber(orders.pagination.total)} records after filters</span>
        </div>
        <label className="page-size-control">
          <span>Rows</span>
          <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={25}>25</option>
          </select>
        </label>
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th aria-label="Expand row" />
              {columns.map((column) => (
                <th key={column.key}>
                  <button
                    type="button"
                    className={sort.sortBy === column.key ? 'sort-button active' : 'sort-button'}
                    onClick={() => setSort(column.key)}
                    title={`Sort by ${column.label}`}
                  >
                    {column.label}
                    <ArrowUpDown size={14} aria-hidden="true" />
                  </button>
                </th>
              ))}
              <th>Categories</th>
            </tr>
          </thead>
          <tbody>
            {orders.data.map((order) => (
              <OrderRow
                key={order.order_id}
                order={order}
                expanded={selectedOrderId === order.order_id}
                onToggle={() =>
                  setSelectedOrderId(selectedOrderId === order.order_id ? null : order.order_id)
                }
              />
            ))}
          </tbody>
        </table>
      </div>

      <footer className="pagination-bar">
        <span>
          Page {orders.pagination.page} of {orders.pagination.total_pages}
        </span>
        <div>
          <button
            className="icon-button"
            type="button"
            title="Previous page"
            disabled={!orders.pagination.has_previous}
            onClick={() => setPage(page - 1)}
          >
            <ChevronLeft size={18} aria-hidden="true" />
          </button>
          <button
            className="icon-button"
            type="button"
            title="Next page"
            disabled={!orders.pagination.has_next}
            onClick={() => setPage(page + 1)}
          >
            <ChevronRight size={18} aria-hidden="true" />
          </button>
        </div>
      </footer>
    </section>
  );
}

type OrderRowProps = {
  order: Order;
  expanded: boolean;
  onToggle: () => void;
};

function OrderRow({ order, expanded, onToggle }: OrderRowProps) {
  return (
    <>
      <tr>
        <td>
          <button className="icon-button compact" type="button" onClick={onToggle} title="Toggle details">
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </td>
        <td>{order.order_id}</td>
        <td>
          <strong>{order.customer_name}</strong>
          <small>{order.customer_id}</small>
        </td>
        <td>{formatDate(order.order_date)}</td>
        <td>
          <strong>{formatCurrency(order.total_value, order.base_currency)}</strong>
          <small>{formatCurrency(order.converted_total_value, order.display_currency)}</small>
        </td>
        <td>
          <span className={order.is_delayed ? 'status-pill delayed' : 'status-pill ok'}>
            {order.shipment_status}
          </span>
        </td>
        <td>{order.delivery_days ?? '-'}</td>
        <td>{order.categories.join(', ')}</td>
      </tr>
      {expanded ? (
        <tr className="detail-row">
          <td />
          <td colSpan={7}>
            <div className="line-items">
              {order.items.map((item) => (
                <div className="line-item" key={`${order.order_id}-${item.product_id}`}>
                  <span>
                    <strong>{item.product_name}</strong>
                    <small>{item.category}</small>
                  </span>
                  <span>{formatNumber(item.quantity)} units</span>
                  <span>{formatCurrency(item.unit_price, order.base_currency)} each</span>
                  <strong>{formatCurrency(item.line_total, order.base_currency)}</strong>
                </div>
              ))}
            </div>
          </td>
        </tr>
      ) : null}
    </>
  );
}
