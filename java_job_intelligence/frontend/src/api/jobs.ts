import { saveAs } from 'file-saver';
import { apiClient } from './client';
import type { Company, DashboardStats, JobFilters, PaginatedJobs } from '../types/job';
export async function fetchJobs(filters: JobFilters): Promise<PaginatedJobs> { const { data } = await apiClient.get<PaginatedJobs>('/jobs', { params: filters }); return data; }
export async function fetchCompanies(): Promise<Company[]> { const { data } = await apiClient.get<Company[]>('/companies'); return data; }
export async function fetchStats(): Promise<DashboardStats> { const { data } = await apiClient.get<DashboardStats>('/stats'); return data; }
export async function triggerSync(): Promise<void> { await apiClient.post('/sync', {}); }
export async function exportExcel(filters: JobFilters): Promise<void> { const response = await apiClient.get('/export/excel', { params: filters, responseType: 'blob' }); saveAs(response.data, `java-jobs-${new Date().toISOString().slice(0, 10)}.xlsx`); }
