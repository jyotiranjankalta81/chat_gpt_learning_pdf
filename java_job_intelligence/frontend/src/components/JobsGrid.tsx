import { ModuleRegistry } from '@ag-grid-community/core';
import { ClientSideRowModelModule } from '@ag-grid-community/client-side-row-model';
import { AgGridReact } from '@ag-grid-community/react';
import type { ColDef } from '@ag-grid-community/core';
import '@ag-grid-community/styles/ag-grid.css';
import '@ag-grid-community/styles/ag-theme-quartz.css';
import type { Job } from '../types/job';
ModuleRegistry.registerModules([ClientSideRowModelModule]);
interface Props { jobs: Job[]; }
function companyName(job: Job): string { return typeof job.companyId === 'object' ? job.companyId.name : ''; }
export function JobsGrid({ jobs }: Props) { const columnDefs: ColDef<Job>[] = [{ headerName: 'Company', valueGetter: ({ data }) => data ? companyName(data) : '', sortable: true, filter: true }, { field: 'jobId', headerName: 'Job ID', sortable: true, filter: true }, { field: 'title', headerName: 'Job Title', flex: 1, minWidth: 220, sortable: true, filter: true }, { field: 'location', sortable: true, filter: true }, { headerName: 'Experience', valueGetter: ({ data }) => data ? `${data.experienceMin}-${data.experienceMax} years` : '', sortable: true }, { headerName: 'Skills', valueGetter: ({ data }) => data?.skills.join(', ') ?? '', flex: 1, minWidth: 260 }, { field: 'postedDate', headerName: 'Posted Date', valueFormatter: ({ value }) => value ? String(value).slice(0, 10) : '' }, { field: 'source', sortable: true, filter: true }, { headerName: 'Apply', field: 'applyUrl', cellRenderer: ({ value }: { value: string }) => <a href={value} target="_blank" rel="noreferrer">Apply</a> }]; return <div className="ag-theme-quartz" style={{ height: 560, width: '100%' }}><AgGridReact rowData={jobs} columnDefs={columnDefs} pagination paginationPageSize={25} /></div>; }
