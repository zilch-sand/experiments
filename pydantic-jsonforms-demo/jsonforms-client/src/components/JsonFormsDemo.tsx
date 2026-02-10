import { useEffect, useMemo, useState } from 'react';
import { JsonForms } from '@jsonforms/react';
import {
  Alert,
  Box,
  Button,
  Grid,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import {
  materialCells,
  materialRenderers,
} from '@jsonforms/material-renderers';

const API_BASE =
  import.meta.env.VITE_API_BASE?.toString() ?? 'http://127.0.0.1:8000';

const initialData = {
  meta: {
    title: 'Q2 Portfolio',
    owner_email: 'owner@example.com',
    created_on: '2024-06-01',
    visibility: 'team',
  },
  projects: [
    {
      meta: {
        name: 'Analytics Revamp',
        status: 'active',
        start_date: '2024-03-01',
        end_date: null,
        budget_usd: 250000,
        repo_url: 'https://github.com/example/analytics',
        tags: ['data', 'etl'],
      },
      summary: 'Modernize the analytics pipeline and dashboards.',
      contributors: ['Ada Lovelace', 'Grace Hopper'],
    },
  ],
};

type ApiStatus = {
  state: 'idle' | 'loading' | 'success' | 'error';
  message: string;
};

export const JsonFormsDemo = () => {
  const [schema, setSchema] = useState<Record<string, unknown> | null>(null);
  const [uiSchema, setUiSchema] = useState<Record<string, unknown> | null>(null);
  const [data, setData] = useState(initialData);
  const [errors, setErrors] = useState<unknown[]>([]);
  const [apiStatus, setApiStatus] = useState<ApiStatus>({
    state: 'idle',
    message: '',
  });

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/schema`).then((response) => response.json()),
      fetch(`${API_BASE}/ui-schema`).then((response) => response.json()),
    ])
      .then(([schemaPayload, uiSchemaPayload]) => {
        setSchema(schemaPayload);
        setUiSchema(uiSchemaPayload);
      })
      .catch((error: Error) => {
        setApiStatus({
          state: 'error',
          message: `Failed to load schema: ${error.message}`,
        });
      });
  }, []);

  const stringifiedData = useMemo(
    () => JSON.stringify(data, null, 2),
    [data],
  );
  const stringifiedErrors = useMemo(
    () => JSON.stringify(errors, null, 2),
    [errors],
  );

  const handleValidate = async () => {
    setApiStatus({ state: 'loading', message: 'Validating...' });
    try {
      const response = await fetch(`${API_BASE}/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const payload = await response.json();
      if (!response.ok) {
        const detail = payload?.detail;
        const detailMessage = Array.isArray(detail)
          ? detail
              .map((item) => {
                const path = Array.isArray(item?.loc)
                  ? item.loc.join('.')
                  : 'payload';
                const msg = item?.msg ?? 'Invalid value';
                return `${path}: ${msg}`;
              })
              .join('\n')
          : detail || payload?.message;
        setApiStatus({
          state: 'error',
          message: detailMessage
            ? `Validation failed: ${detailMessage}`
            : 'Validation failed.',
        });
        return;
      }
      setApiStatus({ state: 'success', message: payload.message });
    } catch (error) {
      setApiStatus({
        state: 'error',
        message: `API error: ${(error as Error).message}`,
      });
    }
  };

  if (!schema || !uiSchema) {
    return (
      <Paper elevation={2} sx={{ padding: 4 }}>
        <Typography variant="h6" gutterBottom>
          Loading schema from {API_BASE}...
        </Typography>
        {apiStatus.message ? (
          <Alert severity="error">{apiStatus.message}</Alert>
        ) : null}
      </Paper>
    );
  }

  return (
    <Grid container spacing={3} alignItems="flex-start">
      <Grid item xs={12} lg={6}>
        <Stack spacing={2}>
          <Paper elevation={2} sx={{ padding: 3 }}>
            <Typography variant="h6" className="panel-title">
              Bound data
            </Typography>
            <Box sx={{ backgroundColor: '#f8fafc', padding: 2 }}>
              <pre className="panel-pre">{stringifiedData}</pre>
            </Box>
          </Paper>
          <Paper elevation={2} sx={{ padding: 3 }}>
            <Typography variant="h6" className="panel-title">
              JSONForms errors
            </Typography>
            <Box sx={{ backgroundColor: '#f8fafc', padding: 2 }}>
              <pre className="panel-pre">{stringifiedErrors}</pre>
            </Box>
          </Paper>
        </Stack>
      </Grid>
      <Grid item xs={12} lg={6}>
        <Paper elevation={2} sx={{ padding: 3 }}>
          <Typography variant="h6" className="panel-title">
            Rendered form
          </Typography>
          <JsonForms
            schema={schema}
            uischema={uiSchema}
            data={data}
            renderers={materialRenderers}
            cells={materialCells}
            onChange={({ data: nextData, errors: nextErrors }) => {
              setData(nextData as typeof initialData);
              setErrors(nextErrors ?? []);
            }}
          />
          <Stack direction="row" spacing={2} alignItems="center" mt={2}>
            <Button
              variant="contained"
              onClick={handleValidate}
              disabled={apiStatus.state === 'loading'}>
              Validate with API
            </Button>
            {apiStatus.message ? (
              <Alert
                severity={apiStatus.state === 'success' ? 'success' : 'error'}>
                {apiStatus.message}
              </Alert>
            ) : null}
          </Stack>
        </Paper>
      </Grid>
    </Grid>
  );
};
