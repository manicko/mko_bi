import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { Toaster } from 'react-hot-toast'
import { AppRoutes } from './routes'
import { ErrorBoundary } from '../shared/components/ErrorBoundary'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
})

const theme = createTheme({
  palette: {
    mode: 'light',
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Toaster
            position="top-right"
            gutter={8}
            toastOptions={{
              success: {
                duration: 3000,
              },
              error: {
                duration: 5000,
              },
            }}
          />
          <ErrorBoundary>
            <AppRoutes />
          </ErrorBoundary>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
