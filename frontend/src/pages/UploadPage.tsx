import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ingestMockInbox, uploadInvoices } from '../api/invoices';
import { getErrorMessage } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import type { InvoiceUploadResult } from '../types/invoice';

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [results, setResults] = useState<InvoiceUploadResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function addFiles(newFiles: FileList | null) {
    if (!newFiles) return;
    setFiles((prev) => [...prev, ...Array.from(newFiles)]);
  }

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleUpload() {
    if (files.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      const response = await uploadInvoices(files);
      setResults(response.results);
      setFiles([]);
      if (inputRef.current) inputRef.current.value = '';
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setUploading(false);
    }
  }

  async function handleIngestMock() {
    setIngesting(true);
    setError(null);
    try {
      const response = await ingestMockInbox();
      setResults(response.results);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIngesting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Upload invoices</h1>
        <p className="mt-1 text-sm text-slate-500">
          Upload one or more PDF invoices for AI extraction. Each file is processed independently.
        </p>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <label
          htmlFor="file-input"
          className="flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed border-slate-300 px-6 py-10 text-center hover:border-slate-400"
        >
          <span className="text-sm font-medium text-slate-700">Click to choose PDF files</span>
          <span className="mt-1 text-xs text-slate-400">or drop them here</span>
          <input
            id="file-input"
            ref={inputRef}
            type="file"
            accept="application/pdf"
            multiple
            className="hidden"
            onChange={(e) => addFiles(e.target.files)}
          />
        </label>

        {files.length > 0 && (
          <ul className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
            {files.map((file, i) => (
              <li key={`${file.name}-${i}`} className="flex items-center justify-between px-3 py-2 text-sm">
                <span className="truncate text-slate-700">{file.name}</span>
                <button
                  type="button"
                  onClick={() => removeFile(i)}
                  className="ml-3 shrink-0 text-slate-400 hover:text-red-600"
                  aria-label={`Remove ${file.name}`}
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleUpload}
            disabled={files.length === 0 || uploading}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {uploading ? 'Uploading…' : `Upload ${files.length || ''} file${files.length === 1 ? '' : 's'}`.trim()}
          </button>
          <button
            type="button"
            onClick={handleIngestMock}
            disabled={ingesting}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {ingesting ? 'Ingesting…' : 'Ingest mock inbox'}
          </button>
        </div>

        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>

      {results && (
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="text-base font-semibold text-slate-900">Results</h2>
          <ul className="mt-3 divide-y divide-slate-100">
            {results.map((result) => (
              <li key={result.filename} className="flex items-center justify-between gap-4 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-800">{result.filename}</p>
                  {result.status === 'failed' && result.error && (
                    <p className="mt-0.5 text-xs text-red-600">{result.error}</p>
                  )}
                  {result.status === 'completed' && result.invoice && (
                    <p className="mt-0.5 text-xs text-slate-500">
                      {result.invoice.vendor_name} · {result.invoice.invoice_number}
                    </p>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  <StatusBadge value={result.status} />
                  {result.status === 'completed' && result.invoice && (
                    <Link to={`/invoices/${result.invoice.id}`} className="text-sm font-medium text-slate-900 underline">
                      View
                    </Link>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
