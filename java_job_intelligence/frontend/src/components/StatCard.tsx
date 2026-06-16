import { Card, CardContent, Typography } from '@mui/material';
interface Props { label: string; value: string | number; }
export function StatCard({ label, value }: Props) { return <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}><CardContent><Typography color="text.secondary" variant="body2">{label}</Typography><Typography variant="h4" fontWeight={700}>{value}</Typography></CardContent></Card>; }
