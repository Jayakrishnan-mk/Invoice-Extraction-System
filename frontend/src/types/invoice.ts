// Mirrors backend/app/schemas/invoice.py. Decimal fields are serialized as strings by
// Pydantic, so amounts/quantities are typed as `string` here and parsed at render time.

export interface InvoiceItem {
  id: string;
  description: string;
  material_type: string | null;
  quantity: string;
  unit: string;
  unit_price: string;
  line_total: string;
}

export interface Invoice {
  id: string;
  vendor_name: string;
  vendor_email: string | null;
  invoice_number: string;
  invoice_date: string | null;
  material_type: string;
  subtotal_amount: string;
  tax_amount: string;
  total_amount: string;
  currency: string;
  status: string;
  payment_status: string;
  source_filename: string;
  llm_model: string;
  processed_at: string;
  processing_time_ms: number | null;
  created_at: string;
  updated_at: string;
  items: InvoiceItem[];
}

export interface InvoiceDetail extends Invoice {
  source_file_path: string;
  raw_text: string;
  structured_json: Record<string, unknown>;
}

export interface InvoiceListItem {
  id: string;
  vendor_name: string;
  invoice_number: string;
  invoice_date: string | null;
  material_type: string;
  total_amount: string;
  currency: string;
  status: string;
  payment_status: string;
  source_filename: string;
  created_at: string;
}

export interface InvoiceListResponse {
  items: InvoiceListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface InvoiceListParams {
  vendor?: string;
  material_type?: string;
  status?: string;
  payment_status?: string;
  date_from?: string;
  date_to?: string;
  min_amount?: string;
  max_amount?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface InvoiceUploadResult {
  filename: string;
  status: 'completed' | 'failed';
  invoice: Invoice | null;
  error: string | null;
}

export interface InvoiceUploadResponse {
  results: InvoiceUploadResult[];
}
