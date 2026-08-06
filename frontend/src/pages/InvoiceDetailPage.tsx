import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getInvoice } from '../api/invoices';
import { getErrorMessage } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import { formatDate, formatDateTime, formatMoney } from '../utils/format';
import type { InvoiceDetail } from '../types/invoice';

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-500">{label}</dt>
      <dd className="mt-0.5 text-sm text-slate-800">{value}</dd>
    </div>
  );
}

export default function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    getInvoice(id)
      .then(setInvoice)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-sm text-slate-500">Loading…</p>;

  if (error) {
    return (
      <div className="space-y-3">
        <Link to="/" className="text-sm text-slate-500 underline">
          ← Back to invoices
        </Link>
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!invoice) return null;

  return (
    <div className="space-y-6">
      <div>
        <Link to="/" className="text-sm text-slate-500 underline">
          ← Back to invoices
        </Link>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">{invoice.vendor_name}</h1>
            <p className="text-sm text-slate-500">Invoice {invoice.invoice_number}</p>
          </div>
          <div className="flex gap-2">
            <StatusBadge value={invoice.status} />
            <StatusBadge value={invoice.payment_status} />
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          <Field label="Vendor email" value={invoice.vendor_email ?? '—'} />
          <Field label="Invoice date" value={formatDate(invoice.invoice_date)} />
          <Field label="Material type" value={invoice.material_type} />
          <Field label="Currency" value={invoice.currency} />
          <Field label="Subtotal" value={formatMoney(invoice.subtotal_amount, invoice.currency)} />
          <Field label="Tax" value={formatMoney(invoice.tax_amount, invoice.currency)} />
          <Field label="Total" value={formatMoney(invoice.total_amount, invoice.currency)} />
          <Field label="Source file" value={invoice.source_filename} />
          <Field label="LLM model" value={invoice.llm_model} />
          <Field
            label="Processing time"
            value={invoice.processing_time_ms !== null ? `${invoice.processing_time_ms} ms` : '—'}
          />
          <Field label="Processed at" value={formatDateTime(invoice.processed_at)} />
          <Field label="Created at" value={formatDateTime(invoice.created_at)} />
        </dl>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="text-base font-semibold text-slate-900">Line items</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <tr>
                <th className="py-2 pr-4 font-medium">Description</th>
                <th className="py-2 pr-4 font-medium">Material</th>
                <th className="py-2 pr-4 font-medium">Qty</th>
                <th className="py-2 pr-4 font-medium">Unit</th>
                <th className="py-2 pr-4 font-medium">Unit price</th>
                <th className="py-2 pr-4 font-medium">Line total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {invoice.items.map((item) => (
                <tr key={item.id}>
                  <td className="py-2 pr-4 text-slate-800">{item.description}</td>
                  <td className="py-2 pr-4 text-slate-600">{item.material_type ?? '—'}</td>
                  <td className="py-2 pr-4 text-slate-600">{item.quantity}</td>
                  <td className="py-2 pr-4 text-slate-600">{item.unit}</td>
                  <td className="py-2 pr-4 text-slate-600">{formatMoney(item.unit_price, invoice.currency)}</td>
                  <td className="py-2 pr-4 font-medium text-slate-800">
                    {formatMoney(item.line_total, invoice.currency)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <details className="rounded-lg border border-slate-200 bg-white p-6">
        <summary className="cursor-pointer text-base font-semibold text-slate-900">Structured JSON (Gemini output)</summary>
        <pre className="mt-3 max-h-96 overflow-auto rounded-md bg-slate-50 p-3 text-xs text-slate-700">
          {JSON.stringify(invoice.structured_json, null, 2)}
        </pre>
      </details>

      <details className="rounded-lg border border-slate-200 bg-white p-6">
        <summary className="cursor-pointer text-base font-semibold text-slate-900">Raw extracted text</summary>
        <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-xs text-slate-700">
          {invoice.raw_text}
        </pre>
      </details>
    </div>
  );
}
