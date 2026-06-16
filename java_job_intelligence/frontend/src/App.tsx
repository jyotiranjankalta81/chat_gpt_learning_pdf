import { CssBaseline, ThemeProvider } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { AppRoutes } from './routes/AppRoutes';
import { theme } from './theme/theme';
const queryClient = new QueryClient();
export function App() { return <QueryClientProvider client={queryClient}><ThemeProvider theme={theme}><CssBaseline /><BrowserRouter><AppRoutes /></BrowserRouter></ThemeProvider></QueryClientProvider>; }
