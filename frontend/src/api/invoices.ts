import { apiClient } from './client';
import type {
  InvoiceDetail,
  InvoiceListParams,
  InvoiceListResponse,
  InvoiceUploadResponse,
} from '../types/invoice';

export async function uploadInvoices(files: File[]): Promise<InvoiceUploadResponse> {
  const formData = new FormData();
  for (const file of files) formData.append('files', file);
  const { data } = await apiClient.post<InvoiceUploadResponse>('/invoices/upload', formData);
  return data;
}

export async function ingestMockInbox(): Promise<InvoiceUploadResponse> {
  const { data } = await apiClient.post<InvoiceUploadResponse>('/invoices/ingest-mock');
  return data;
}

export async function listInvoices(params: InvoiceListParams): Promise<InvoiceListResponse> {
  const { data } = await apiClient.get<InvoiceListResponse>('/invoices', { params });
  return data;
}

export async function listVendors(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>('/invoices/vendors');
  return data;
}

export async function listMaterials(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>('/invoices/materials');
  return data;
}

export async function getInvoice(id: string): Promise<InvoiceDetail> {
  const { data } = await apiClient.get<InvoiceDetail>(`/invoices/${id}`);
  return data;
}
