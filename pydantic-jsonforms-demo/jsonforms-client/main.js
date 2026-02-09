import React, { useEffect, useMemo, useState } from "https://esm.sh/react@18";
import { createRoot } from "https://esm.sh/react-dom@18/client";
import { JsonForms } from "https://esm.sh/@jsonforms/react@3.3.0";
import { vanillaCells, vanillaRenderers } from "https://esm.sh/@jsonforms/vanilla-renderers@3.3.0";

const API_BASE = "http://localhost:8000";

const uiSchema = {
  type: "VerticalLayout",
  elements: [
    {
      type: "Group",
      label: "Portfolio",
      elements: [
        { type: "Control", scope: "#/properties/meta/properties/title" },
        { type: "Control", scope: "#/properties/meta/properties/owner_email" },
        { type: "Control", scope: "#/properties/meta/properties/created_on" },
        { type: "Control", scope: "#/properties/meta/properties/visibility" }
      ]
    },
    {
      type: "Group",
      label: "Projects",
      elements: [{ type: "Control", scope: "#/properties/projects" }]
    }
  ]
};

const initialData = {
  meta: {
    title: "Q2 Portfolio",
    owner_email: "owner@example.com",
    created_on: "2024-06-01",
    visibility: "team"
  },
  projects: [
    {
      meta: {
        name: "Analytics Revamp",
        status: "active",
        start_date: "2024-03-01",
        end_date: null,
        budget_usd: 250000,
        repo_url: "https://github.com/example/analytics",
        tags: ["data", "etl"]
      },
      summary: "Modernize the analytics pipeline and dashboards.",
      contributors: ["Ada Lovelace", "Grace Hopper"]
    }
  ]
};

function App() {
  const [schema, setSchema] = useState(null);
  const [data, setData] = useState(initialData);
  const [errors, setErrors] = useState([]);
  const [apiStatus, setApiStatus] = useState({ state: "idle", message: "" });

  useEffect(() => {
    fetch(`${API_BASE}/schema`)
      .then((response) => response.json())
      .then((payload) => setSchema(payload))
      .catch((error) => {
        setApiStatus({
          state: "error",
          message: `Failed to load schema: ${error.message}`
        });
      });
  }, []);

  const canValidate = useMemo(() => schema !== null, [schema]);

  const handleValidate = async () => {
    setApiStatus({ state: "loading", message: "Validating..." });
    try {
      const response = await fetch(`${API_BASE}/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      const payload = await response.json();
      if (!response.ok) {
        setApiStatus({ state: "error", message: "Validation failed." });
        setErrors(payload.detail ?? []);
        return;
      }
      setApiStatus({ state: "success", message: payload.message });
      setErrors([]);
    } catch (error) {
      setApiStatus({ state: "error", message: `API error: ${error.message}` });
    }
  };

  if (!schema) {
    return (
      <div className="panel">
        <p>Loading schema from {API_BASE}/schema...</p>
        {apiStatus.message && <p className="status">{apiStatus.message}</p>}
      </div>
    );
  }

  return (
    <>
      <div className="panel">
        <JsonForms
          schema={schema}
          uischema={uiSchema}
          data={data}
          renderers={vanillaRenderers}
          cells={vanillaCells}
          onChange={({ data: nextData, errors: nextErrors }) => {
            setData(nextData);
            setErrors(nextErrors ?? []);
          }}
        />
        <button onClick={handleValidate} disabled={!canValidate}>
          Validate with API
        </button>
        {apiStatus.message && <p className="status">{apiStatus.message}</p>}
      </div>
      <div className="panel">
        <h2>Current JSON</h2>
        <pre>{JSON.stringify(data, null, 2)}</pre>
        <h2>JSONForms Errors</h2>
        <pre>{JSON.stringify(errors, null, 2)}</pre>
      </div>
    </>
  );
}

const root = createRoot(document.getElementById("root"));
root.render(<App />);
