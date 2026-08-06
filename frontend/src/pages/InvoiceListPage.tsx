import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listInvoices, listMaterials, listVendors } from '../api/invoices';
import { getErrorMessage } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import { formatDate, formatMoney } from '../utils/format';
import type { InvoiceListItem, InvoiceListParams } from '../types/invoice';

const PAGE_SIZE = 20;

const emptyFilters: InvoiceListParams = {
  vendor: '',
  material_type: '',
  payment_status: '',
  date_from: '',
  date_to: '',
  min_amount: '',
  max_amount: '',
  search: '',
};

function cleanParams(filters: InvoiceListParams, page: number): InvoiceListParams {
  const params: InvoiceListParams = { page, page_size: PAGE_SIZE };
  for (const [key, value] of Object.entries(filters)) {
    if (value !== '' && value !== undefined) {
      (params as Record<string, unknown>)[key] = value;
    }
  }
  return params;
}

export default function InvoiceListPage() {
  const [draft, setDraft] = useState<InvoiceListParams>(emptyFilters);
  const [appliedFilters, setAppliedFilters] = useState<InvoiceListParams>(emptyFilters);
  const [page, setPage] = useState(1);

  const [items, setItems] = useState<InvoiceListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [vendors, setVendors] = useState<string[]>([]);
  const [materials, setMaterials] = useState<string[]>([]);

  useEffect(() => {
    listVendors().then(setVendors).catch(() => {});
    listMaterials().then(setMaterials).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listInvoices(cleanParams(appliedFilters, page))
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
        setTotalPages(res.total_pages);
      })
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [appliedFilters, page]);

  function handleApply(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    setAppliedFilters(draft);
  }

  function handleReset() {
    setDraft(emptyFilters);
    setAppliedFilters(emptyFilters);
    setPage(1);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Invoices</h1>
        <p className="mt-1 text-sm text-slate-500">
          {loading ? 'Loading…' : `${total} invoice${total === 1 ? '' : 's'} found`}
        </p>
      </div>

      <form onSubmit={handleApply} className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="block text-xs font-medium text-slate-500">Search</label>
            <input
              type="text"
              placeholder="Vendor, invoice #, text…"
              value={draft.search}
              onChange={(e) => setDraft({ ...draft, search: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500">Vendor</label>
            <input
              list="vendor-options"
              value={draft.vendor}
              onChange={(e) => setDraft({ ...draft, vendor: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm"
            />
            <datalist id="vendor-options">
              {vendors.map((v) => (
                <option key={v} value={v} />
              ))}
            </datalist>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500">Material type</label>
            <select
              value={draft.material_type}
              onChange={(e) => setDraft({ ...draft, material_type: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm"
            >
              <option value="">All</option>
              {materials.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500">Payment status</label>
            <select
              value={draft.payment_status}
              onChange={(e) => setDraft({ ...draft, payment_status: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm"
            >
              <option value="">All</option>
              <option value="paid">Paid</option>
              <option value="unpaid">Unpaid</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500">Date from</label>
            <input
              type="date"
              value={draft.date_from}
              onChange={(e) => setDraft({ ...draft, date_from: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500">Date to</label>
            <input
              type="date"
              value={draft.date_to}
              onChange={(e) => setDraft({ ...draft, date_to: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500">Min amount</label>
            <input
              type="number"
              min="0"
              value={draft.min_amount}
              onChange={(e) => setDraft({ ...draft, min_amount: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500">Max amount</label>
            <input
              type="number"
              min="0"
              value={draft.max_amount}
              onChange={(e) => setDraft({ ...draft, max_amount: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm"
            />
          </div>
        </div>
        <div className="mt-4 flex gap-3">
          <button
            type="submit"
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
          >
            Apply filters
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Reset
          </button>
        </div>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full min-w-[800px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2.5 font-medium">Vendor</th>
              <th className="px-4 py-2.5 font-medium">Invoice #</th>
              <th className="px-4 py-2.5 font-medium">Date</th>
              <th className="px-4 py-2.5 font-medium">Material</th>
              <th className="px-4 py-2.5 font-medium">Total</th>
              <th className="px-4 py-2.5 font-medium">Payment</th>
              <th className="px-4 py-2.5 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                  No invoices match these filters.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-slate-50">
                <td className="px-4 py-2.5 text-slate-800">{item.vendor_name}</td>
                <td className="px-4 py-2.5 text-slate-600">{item.invoice_number}</td>
                <td className="px-4 py-2.5 text-slate-600">{formatDate(item.invoice_date)}</td>
                <td className="px-4 py-2.5 text-slate-600">{item.material_type}</td>
                <td className="px-4 py-2.5 font-medium text-slate-800">
                  {formatMoney(item.total_amount, item.currency)}
                </td>
                <td className="px-4 py-2.5">
                  <StatusBadge value={item.payment_status} />
                </td>
                <td className="px-4 py-2.5 text-right">
                  <Link to={`/invoices/${item.id}`} className="font-medium text-slate-900 underline">
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-slate-600">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded-md border border-slate-300 px-3 py-1.5 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Previous
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-md border border-slate-300 px-3 py-1.5 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
