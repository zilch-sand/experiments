import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { createRoot } from 'react-dom/client';
import App from './App';
import { StrictMode } from 'react';

const theme = createTheme({
  components: {
    MuiFormControl: {
      styleOverrides: {
        root: {
          margin: '0.75rem 0',
        },
      },
    },
  },
});

const rootEl = document.getElementById('root');

if (!rootEl) throw new Error('Failed to find the root element');

createRoot(rootEl).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </StrictMode>,
);
