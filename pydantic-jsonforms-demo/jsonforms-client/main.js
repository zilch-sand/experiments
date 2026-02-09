import React, { useEffect, useMemo, useState } from "https://esm.sh/react@18";
import { createRoot } from "https://esm.sh/react-dom@18/client";
import { JsonForms } from "https://esm.sh/@jsonforms/react@3.7.0";
import { materialCells, materialRenderers } from "https://esm.sh/@jsonforms/material-renderers";

const h = React.createElement;

const API_BASE = "http://127.0.0.1:8000";

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
  const [uiSchema, setUiSchema] = useState(null);
  const [data, setData] = useState(initialData);
  const [errors, setErrors] = useState([]);
  const [apiStatus, setApiStatus] = useState({ state: "idle", message: "" });

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/schema`).then((response) => response.json()),
      fetch(`${API_BASE}/ui-schema`).then((response) => response.json())
    ])
      .then(([schemaPayload, uiSchemaPayload]) => {
        setSchema(schemaPayload);
        setUiSchema(uiSchemaPayload);
      })
      .catch((error) => {
        setApiStatus({
          state: "error",
          message: `Failed to load schema: ${error.message}`
        });
      });
  }, []);

  const canValidate = useMemo(() => schema !== null && uiSchema !== null, [
    schema,
    uiSchema
  ]);

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
        const detail = payload?.detail;
        const detailMessage = Array.isArray(detail)
          ? detail
              .map((item) => {
                const path = Array.isArray(item?.loc)
                  ? item.loc.join(".")
                  : "payload";
                const msg = item?.msg ?? "Invalid value";
                return `${path}: ${msg}`;
              })
              .join("\n")
          : detail || payload?.message;
        setApiStatus({
          state: "error",
          message: detailMessage ? `Validation failed: ${detailMessage}` : "Validation failed."
        });
        setErrors(detail ?? []);
        return;
      }
      setApiStatus({ state: "success", message: payload.message });
      setErrors([]);
    } catch (error) {
      setApiStatus({ state: "error", message: `API error: ${error.message}` });
    }
  };

  if (!schema || !uiSchema) {
    return h(
      "div",
      { className: "panel" },
      h("p", null, `Loading schema from ${API_BASE}/schema...`),
      apiStatus.message ? h("p", { className: "status" }, apiStatus.message) : null
    );
  }

  return h(
    React.Fragment,
    null,
    h(
      "div",
      { className: "panel" },
      h(JsonForms, {
        schema,
        uischema: uiSchema,
        data,
        renderers: materialRenderers,
        cells: materialCells,
        onChange: ({ data: nextData, errors: nextErrors }) => {
          setData(nextData);
          setErrors(nextErrors ?? []);
        }
      }),
      h(
        "button",
        { onClick: handleValidate, disabled: !canValidate },
        "Validate with API"
      ),
      apiStatus.message ? h("p", { className: "status" }, apiStatus.message) : null
    ),
    h(
      "div",
      { className: "panel" },
      h("h2", null, "Current JSON"),
      h("pre", null, JSON.stringify(data, null, 2)),
      h("h2", null, "JSONForms Errors"),
      h("pre", null, JSON.stringify(errors, null, 2))
    )
  );
}

const root = createRoot(document.getElementById("root"));
root.render(h(App));
