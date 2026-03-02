"""
LLM Classification Shiny App – main entry point.
"""
from __future__ import annotations

import io
import time
from typing import Optional

import pandas as pd
from shiny import App, Inputs, Outputs, Session, reactive, render, ui
import shinyswatch

from .models import MODELS, estimate_cost, get_price
from .prompt_builder import build_prompt, validate_prompt, get_prompt_columns
from .classification import classify_row, fuzzy_match_label
from .batch_manager import BatchManager, BatchJob
from .arena import ArenaConfig, ContestantConfig, run_arena_row, judge_responses, DEFAULT_JUDGE_PROMPT
from .config import DEMO_MODE, GCS_BUCKET, BQ_DATASET

# ---------------------------------------------------------------------------
# Helper constants
# ---------------------------------------------------------------------------

MODEL_NAMES = list(MODELS.keys())
_DEFAULT_PROMPT = (
    "Classify the following text into one of the provided categories.\n\n"
    "Text: {text}\n\n"
    "{label_options}\n\n"
    "Respond with only the category name."
)
_DEFAULT_CATEGORIES = "Positive\nNegative\nNeutral"

_FEEDBACK_SYSTEM = (
    "You are an expert prompt engineer specialising in LLM classification tasks."
)
_FEEDBACK_PROMPT_TEMPLATE = """Review the following classification prompt and categories.

PROMPT:
{prompt}

CATEGORIES:
{categories}

Provide concise feedback on:
1. Clarity – is the task unambiguous?
2. Category overlap – could a sample belong to multiple categories?
3. Missing category – should there be an "Other" / "None of the above" option?
4. Length – if the prompt is very long, suggest using Retrieval-Augmented Generation (RAG) instead.
5. Formatting – is the output format instruction explicit?

Be direct and constructive."""


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _model_card(model_name: str, model_id: str) -> ui.Tag:
    inp, out = get_price(model_id)
    price_str = f"${inp:.3f} / ${out:.3f} per M tokens" if inp or out else "pricing N/A"
    return ui.div(
        ui.strong(model_name),
        ui.span(f" — {price_str}", class_="text-muted small"),
        class_="py-1",
    )


def _thinking_ui(show: bool = False) -> ui.Tag:
    return ui.div(
        ui.input_slider(
            "thinking_level",
            "Thinking depth",
            min=0, max=3, value=0, step=1,
            ticks=True,
        ),
        ui.p(
            ui.tags.small("0=off, 1=1K tokens, 2=8K tokens, 3=32K tokens", class_="text-muted")
        ),
        id="thinking_container",
        style="" if show else "display:none;",
    )


# ---------------------------------------------------------------------------
# UI definition
# ---------------------------------------------------------------------------

app_ui = ui.page_navbar(
    # ── Tab 1: Setup & Test ────────────────────────────────────────────────
    ui.nav_panel(
        "Setup & Test",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("📂 Data"),
                ui.input_file("csv_file", "Upload CSV", accept=[".csv"]),
                ui.output_ui("col_chips"),

                ui.hr(),
                ui.h5("📝 Prompt"),
                ui.input_text_area(
                    "prompt_template",
                    "Prompt template",
                    value=_DEFAULT_PROMPT,
                    rows=8,
                    placeholder="Use {col_name} for CSV columns, {label_options} for categories.",
                ),
                ui.output_ui("prompt_warnings"),

                ui.hr(),
                ui.h5("🏷️ Categories"),
                ui.input_text_area(
                    "categories_text",
                    "Categories (one per line)",
                    value=_DEFAULT_CATEGORIES,
                    rows=5,
                ),
                ui.input_radio_buttons(
                    "label_mode",
                    "Label mode",
                    choices={"single": "Single label", "multi": "Multi label"},
                    selected="single",
                    inline=True,
                ),

                ui.hr(),
                ui.h5("🤖 Model"),
                ui.input_select("model_select", "Model", choices=MODEL_NAMES, selected=MODEL_NAMES[0]),
                ui.output_ui("thinking_ui"),

                ui.hr(),
                ui.h5("▶️ Test run"),
                ui.input_numeric("test_rows", "Test rows", value=5, min=1, max=100),
                ui.input_action_button("run_test", "Run Test", class_="btn-primary w-100"),

                width=380,
            ),
            # Main panel
            ui.div(
                ui.h4("Prompt Preview"),
                ui.output_ui("prompt_preview"),

                ui.div(
                    ui.output_ui("cost_estimate"),
                    class_="mt-2 mb-3",
                ),

                ui.output_ui("test_progress"),

                ui.h4("Test Results", class_="mt-3"),
                ui.output_data_frame("test_results_table"),

                ui.div(
                    ui.input_action_button(
                        "get_feedback_btn",
                        "✨ Get AI Feedback on Prompt",
                        class_="btn-outline-primary mt-3",
                    ),
                    id="feedback_btn_area",
                ),
            ),
        ),
    ),

    # ── Tab 2: Batch Run ───────────────────────────────────────────────────
    ui.nav_panel(
        "Batch Run",
        ui.layout_columns(
            ui.card(
                ui.card_header("⚙️ Batch Settings"),
                ui.input_text("gcs_bucket", "GCS Bucket (gs://…)", value=GCS_BUCKET),
                ui.input_text("bq_dataset", "BigQuery Dataset (project.dataset)", value=BQ_DATASET),
                ui.div(
                    ui.input_action_button("send_batch", "🚀 Send Batch", class_="btn-success me-2"),
                    ui.input_action_button("refresh_batch", "🔄 Refresh Status", class_="btn-outline-secondary"),
                    class_="d-flex gap-2 mt-2",
                ),
                ui.output_ui("batch_send_status"),
            ),
            ui.card(
                ui.card_header("📋 Batch Jobs"),
                ui.output_data_frame("batch_jobs_table"),
                ui.div(
                    ui.input_action_button("download_results_btn", "⬇ Download Results", class_="btn-outline-primary me-2"),
                    ui.download_button("save_classified_csv", "💾 Save Classified CSV", class_="btn-outline-success"),
                    class_="d-flex gap-2 mt-2",
                ),
            ),
            col_widths=[4, 8],
        ),
    ),

    # ── Tab 3: Arena ──────────────────────────────────────────────────────
    ui.nav_panel(
        "Arena",
        ui.layout_columns(
            # Left: configuration
            ui.card(
                ui.card_header("🥊 Add Contestant"),
                ui.input_select("arena_model", "Model", choices=MODEL_NAMES),
                ui.output_ui("arena_thinking_ui"),
                ui.input_text("arena_label", "Display label (optional)", placeholder="e.g. Flash-thinking"),
                ui.input_action_button("add_contestant", "➕ Add", class_="btn-secondary w-100 mt-1"),
                ui.hr(),
                ui.h6("Contestants"),
                ui.output_ui("contestants_list"),
                ui.hr(),
                ui.h6("🧑‍⚖️ Judge"),
                ui.input_select("judge_model", "Judge model", choices=MODEL_NAMES, selected=MODEL_NAMES[0]),
                ui.input_text_area("judge_prompt", "Judge prompt", value=DEFAULT_JUDGE_PROMPT, rows=6),
                ui.hr(),
                ui.input_numeric("arena_rows", "Test rows", value=5, min=1, max=50),
                ui.input_action_button("run_arena", "⚔️ Run Arena", class_="btn-danger w-100"),
            ),
            # Right: results
            ui.card(
                ui.card_header("📊 Arena Results"),
                ui.output_ui("arena_progress"),
                ui.output_data_frame("arena_results_table"),
                ui.h5("💰 Cost Summary", class_="mt-3"),
                ui.output_ui("arena_cost_summary"),
                ui.download_button("export_arena", "📥 Export Arena Data (CSV)", class_="btn-outline-secondary mt-2"),
            ),
            col_widths=[4, 8],
        ),
    ),

    # ── Tab 4: AI Feedback ────────────────────────────────────────────────
    ui.nav_panel(
        "AI Feedback",
        ui.layout_columns(
            ui.card(
                ui.card_header("🔍 Prompt Under Review"),
                ui.output_ui("feedback_prompt_display"),
                ui.input_action_button("get_feedback", "✨ Get AI Feedback", class_="btn-primary w-100 mt-2"),
                ui.output_ui("feedback_spinner"),
            ),
            ui.card(
                ui.card_header("📣 Feedback"),
                ui.output_ui("feedback_output"),
            ),
            col_widths=[4, 8],
        ),
    ),

    title=ui.span(" 🏷️ LLM Classifier"),
    theme=shinyswatch.theme.flatly(),
    id="main_nav",
    fillable=True,
)


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

def server(input: Inputs, output: Outputs, session: Session):
    # ── Reactive state ──────────────────────────────────────────────────────
    loaded_df: reactive.Value[Optional[pd.DataFrame]] = reactive.value(None)
    test_results: reactive.Value[Optional[pd.DataFrame]] = reactive.value(None)
    arena_results: reactive.Value[Optional[pd.DataFrame]] = reactive.value(None)
    arena_contestants: reactive.Value[list[dict]] = reactive.value([])
    feedback_text: reactive.Value[str] = reactive.value("")
    batch_mgr = BatchManager()

    # ── Computed helpers ────────────────────────────────────────────────────

    @reactive.calc
    def current_model():
        return MODELS[input.model_select()]

    @reactive.calc
    def categories():
        return [c.strip() for c in input.categories_text().splitlines() if c.strip()]

    @reactive.calc
    def is_multi():
        return input.label_mode() == "multi"

    # ── Tab 1 outputs ───────────────────────────────────────────────────────

    @render.ui
    def col_chips():
        df = loaded_df()
        if df is None:
            return ui.p("No CSV loaded.", class_="text-muted small")
        chips = [
            ui.span(col, class_="badge bg-secondary me-1 mb-1")
            for col in df.columns
        ]
        return ui.div(ui.p("Available columns:", class_="small fw-bold"), *chips)

    @render.ui
    def prompt_warnings():
        df = loaded_df()
        cols = list(df.columns) if df is not None else []
        warnings = validate_prompt(input.prompt_template(), cols)
        if not warnings:
            return ui.div()
        items = [ui.tags.li(w) for w in warnings]
        return ui.div(
            ui.tags.ul(*items, class_="mb-0 ps-3"),
            class_="alert alert-warning py-2 small",
        )

    @render.ui
    def thinking_ui():
        model = current_model()
        return _thinking_ui(show=model.supports_thinking)

    @render.ui
    def prompt_preview():
        df = loaded_df()
        template = input.prompt_template()
        cats = categories()
        if df is None or df.empty:
            preview = build_prompt(template, {}, cats, is_multi())
        else:
            preview = build_prompt(template, df.iloc[0].to_dict(), cats, is_multi())
        return ui.div(
            ui.tags.pre(preview, style="white-space:pre-wrap; font-size:0.85rem; background:#f8f9fa; padding:1rem; border-radius:4px;"),
        )

    @render.ui
    def cost_estimate():
        df = loaded_df()
        model = current_model()
        template = input.prompt_template()
        cats = categories()
        if df is None or df.empty:
            return ui.div()
        # Use first row as token estimate proxy
        sample_prompt = build_prompt(template, df.iloc[0].to_dict(), cats, is_multi())
        from .vertex_client import count_tokens
        approx_input = count_tokens(model, sample_prompt)
        approx_output = 15  # typical short label response
        cost_per_row = estimate_cost(model.id, approx_input, approx_output)
        total_cost = cost_per_row * len(df)
        return ui.div(
            ui.span(f"~{approx_input} input tokens/row · ~{approx_output} output tokens/row", class_="badge bg-info me-2"),
            ui.span(f"Est. total cost for {len(df)} rows: ${total_cost:.4f}", class_="badge bg-success"),
        )

    @render.ui
    def test_progress():
        return ui.div(id="test_progress_area")

    @render.data_frame
    def test_results_table():
        df = test_results()
        if df is None:
            return render.DataGrid(pd.DataFrame())
        return render.DataGrid(df, width="100%", height="400px")

    # ── File upload ─────────────────────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.csv_file)
    def _load_csv():
        file_info = input.csv_file()
        if file_info is None:
            return
        path = file_info[0]["datapath"]
        try:
            df = pd.read_csv(path)
            loaded_df.set(df)
        except Exception as exc:
            ui.notification_show(f"Failed to load CSV: {exc}", type="error")

    # ── Run Test ─────────────────────────────────────────────────────────────

    @reactive.effect
    @reactive.event(input.run_test)
    def _run_test():
        df = loaded_df()
        cats = categories()
        template = input.prompt_template()
        model = current_model()
        n_rows = int(input.test_rows())
        thinking_level = int(input.thinking_level()) if model.supports_thinking else 0

        if df is None or df.empty:
            ui.notification_show("Please upload a CSV first.", type="warning")
            return
        if not cats:
            ui.notification_show("Please enter at least one category.", type="warning")
            return

        sample = df.head(n_rows)
        rows_out = []
        for _, row in sample.iterrows():
            prompt = build_prompt(template, row.to_dict(), cats, is_multi())
            try:
                result = classify_row(model, prompt, cats, is_multi(), thinking_level)
            except Exception as exc:
                result = {
                    "raw_response": f"ERROR: {exc}",
                    "matched_label": "ERROR",
                    "input_tokens": 0,
                    "output_tokens": 0,
                }
            # keep only prompt-referenced cols + classification cols
            ref_cols = get_prompt_columns(template)
            row_data = {c: row.get(c, "") for c in ref_cols if c != "label_options" and c in df.columns}
            row_data.update({
                "raw_response": result["raw_response"],
                "matched_label": result["matched_label"],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
            })
            rows_out.append(row_data)

        test_results.set(pd.DataFrame(rows_out))
        ui.notification_show(f"Test run complete: {len(rows_out)} rows classified.", type="message")

    # ── AI Feedback button on Setup tab ─────────────────────────────────────

    @reactive.effect
    @reactive.event(input.get_feedback_btn)
    def _trigger_feedback_from_test():
        ui.update_navs("main_nav", selected="AI Feedback")

    # ── Tab 2 outputs ───────────────────────────────────────────────────────

    @render.data_frame
    def batch_jobs_table():
        jobs = batch_mgr.list_jobs()
        if not jobs:
            return render.DataGrid(pd.DataFrame(columns=["id", "model_id", "status", "total_rows", "created_at"]))
        rows = [
            {
                "id": j.id[:20] + "…" if len(j.id) > 20 else j.id,
                "model": j.model_id,
                "status": j.status,
                "rows": j.total_rows,
                "created": j.created_at[:19],
            }
            for j in jobs
        ]
        return render.DataGrid(pd.DataFrame(rows), width="100%")

    @render.ui
    def batch_send_status():
        return ui.div(id="batch_status_msg")

    @reactive.effect
    @reactive.event(input.send_batch)
    def _send_batch():
        df = loaded_df()
        cats = categories()
        template = input.prompt_template()
        model = current_model()

        if df is None or df.empty:
            ui.notification_show("Please upload a CSV first.", type="warning")
            return

        prompts = []
        for i, row in df.iterrows():
            prompt = build_prompt(template, row.to_dict(), cats, is_multi())
            prompts.append({"row_index": i, "prompt": prompt})

        gcs_uri = input.gcs_bucket() or "gs://demo-bucket/llm-classifier"
        bq_table = input.bq_dataset() or "demo_dataset.batch_results"

        from .vertex_client import create_batch_job
        try:
            job_id = create_batch_job(model, prompts, bq_table, gcs_uri)
        except Exception as exc:
            ui.notification_show(f"Batch submission failed: {exc}", type="error")
            return

        job = BatchJob(
            id=job_id,
            model_id=model.id,
            status="running",
            total_rows=len(df),
            gcs_uri=gcs_uri,
            bq_table=bq_table,
        )
        batch_mgr.add_job(job)
        ui.notification_show(f"Batch submitted: {job_id}", type="message")

    @reactive.effect
    @reactive.event(input.refresh_batch)
    def _refresh_batch():
        from .vertex_client import get_batch_status
        for job in batch_mgr.list_jobs():
            if job.status in ("running", "pending"):
                model = next((m for m in MODELS.values() if m.id == job.model_id), None)
                if model is None:
                    continue
                try:
                    status = get_batch_status(model, job.id)
                    new_status = "completed" if status["completed"] and status["state"] == "JOB_STATE_SUCCEEDED" else (
                        "failed" if "FAILED" in status["state"] or "CANCELLED" in status["state"] else "running"
                    )
                    batch_mgr.update_job(job.id, status=new_status, output_file=status.get("output_uri") or "")
                except Exception:
                    pass
        ui.notification_show("Batch status refreshed.", type="message")

    @render.download(filename="classified_results.csv")
    def save_classified_csv():
        df = test_results()
        if df is None:
            df = pd.DataFrame()
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        yield buf.getvalue().encode()

    # ── Tab 3: Arena ────────────────────────────────────────────────────────

    @render.ui
    def arena_thinking_ui():
        model = MODELS[input.arena_model()]
        return _thinking_ui(show=model.supports_thinking)

    @render.ui
    def contestants_list():
        contestants = arena_contestants()
        if not contestants:
            return ui.p("No contestants added yet.", class_="text-muted small")
        items = []
        for i, c in enumerate(contestants):
            items.append(
                ui.div(
                    ui.span(c["label"], class_="fw-bold me-2"),
                    ui.span(f"(thinking={c['thinking_level']})", class_="text-muted small me-2"),
                    ui.input_action_button(
                        f"remove_contestant_{i}",
                        "✕",
                        class_="btn btn-sm btn-outline-danger",
                    ),
                    class_="d-flex align-items-center mb-1",
                )
            )
        return ui.div(*items)

    @reactive.effect
    @reactive.event(input.add_contestant)
    def _add_contestant():
        model = MODELS[input.arena_model()]
        label = input.arena_label().strip() or model.display_name
        thinking = int(input.thinking_level()) if model.supports_thinking else 0
        current = list(arena_contestants())
        current.append({
            "model_name": input.arena_model(),
            "label": label,
            "thinking_level": thinking,
        })
        arena_contestants.set(current)
        ui.update_text("arena_label", value="")

    # Dynamic remove buttons
    @reactive.effect
    def _register_remove_handlers():
        contestants = arena_contestants()
        for i in range(len(contestants)):
            btn_id = f"remove_contestant_{i}"
            local_i = i

            @reactive.effect
            @reactive.event(getattr(input, btn_id, lambda: None))
            def _remove(idx=local_i):
                current = list(arena_contestants())
                if idx < len(current):
                    current.pop(idx)
                    arena_contestants.set(current)

    @render.ui
    def arena_progress():
        return ui.div(id="arena_progress_area")

    @reactive.effect
    @reactive.event(input.run_arena)
    def _run_arena():
        df = loaded_df()
        cats = categories()
        template = input.prompt_template()
        contestants = arena_contestants()
        judge_name = input.judge_model()
        judge_model = MODELS[judge_name]
        n_rows = int(input.arena_rows())

        if not contestants:
            ui.notification_show("Add at least one contestant.", type="warning")
            return
        if df is None or df.empty:
            ui.notification_show("Please upload a CSV first.", type="warning")
            return

        contestant_configs = [
            ContestantConfig(
                model_config=MODELS[c["model_name"]],
                thinking_level=c["thinking_level"],
                label=c["label"],
            )
            for c in contestants
        ]
        config = ArenaConfig(
            contestants=contestant_configs,
            judge_model=judge_model,
            judge_prompt=input.judge_prompt(),
            categories=cats,
            multi_label=is_multi(),
        )

        sample = df.head(n_rows)
        rows_out = []
        for row_idx, (_, row) in enumerate(sample.iterrows()):
            prompt = build_prompt(template, row.to_dict(), cats, is_multi())
            responses = run_arena_row(config, prompt, row_idx)
            verdict = judge_responses(config, prompt, responses, row.to_dict())
            row_data: dict = {"row": row_idx}
            for label, info in responses.items():
                row_data[f"{label}_label"] = info["matched_label"]
                row_data[f"{label}_tokens"] = info["input_tokens"] + info["output_tokens"]
                row_data[f"{label}_cost"] = f"${info['cost']:.5f}"
            row_data["judge_verdict"] = verdict
            rows_out.append(row_data)

        arena_results.set(pd.DataFrame(rows_out))
        ui.notification_show("Arena run complete!", type="message")

    @render.data_frame
    def arena_results_table():
        df = arena_results()
        if df is None:
            return render.DataGrid(pd.DataFrame())
        return render.DataGrid(df, width="100%", height="400px")

    @render.ui
    def arena_cost_summary():
        df = arena_results()
        contestants = arena_contestants()
        loaded = loaded_df()
        if df is None or not contestants:
            return ui.p("Run the arena to see cost summary.", class_="text-muted")

        total_rows = len(loaded) if loaded is not None else len(df)
        rows_in_sample = len(df)
        cards = []
        for c in contestants:
            label = c["label"]
            cost_col = f"{label}_cost"
            if cost_col in df.columns:
                sample_cost = df[cost_col].apply(lambda x: float(str(x).replace("$", ""))).sum()
                projected = (sample_cost / rows_in_sample * total_rows) if rows_in_sample else 0
                cards.append(
                    ui.value_box(
                        title=label,
                        value=f"${projected:.4f}",
                        showcase=ui.tags.span("💰"),
                        theme="primary",
                    )
                )
        return ui.layout_columns(*cards, col_widths=[3] * len(cards)) if cards else ui.div()

    @render.download(filename="arena_results.csv")
    def export_arena():
        df = arena_results()
        if df is None:
            df = pd.DataFrame()
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        yield buf.getvalue().encode()

    # ── Tab 4: AI Feedback ──────────────────────────────────────────────────

    @render.ui
    def feedback_prompt_display():
        template = input.prompt_template()
        cats = categories()
        return ui.div(
            ui.h6("Prompt template:"),
            ui.tags.pre(
                template[:600] + ("…" if len(template) > 600 else ""),
                style="font-size:0.8rem; background:#f8f9fa; padding:0.75rem; border-radius:4px; white-space:pre-wrap;",
            ),
            ui.h6("Categories:"),
            ui.p(", ".join(cats) if cats else "—", class_="text-muted"),
        )

    @render.ui
    def feedback_spinner():
        return ui.div(id="feedback_spin_area")

    @render.ui
    def feedback_output():
        text = feedback_text()
        if not text:
            return ui.p("Click 'Get AI Feedback' to analyse your prompt.", class_="text-muted")
        # Render markdown-ish text as paragraphs
        paras = [ui.p(line) for line in text.split("\n") if line.strip()]
        return ui.div(*paras, class_="feedback-result")

    @reactive.effect
    @reactive.event(input.get_feedback, input.get_feedback_btn)
    def _get_feedback():
        template = input.prompt_template()
        cats = categories()
        model = current_model()

        feedback_prompt = _FEEDBACK_PROMPT_TEMPLATE.format(
            prompt=template,
            categories="\n".join(f"- {c}" for c in cats),
        )
        from .vertex_client import call_model as _call
        try:
            result = _call(
                model_config=model,
                prompt=feedback_prompt,
                system_prompt=_FEEDBACK_SYSTEM,
                thinking_level=None,
                max_tokens=1024,
            )
            feedback_text.set(result["text"])
        except Exception as exc:
            feedback_text.set(f"Error getting feedback: {exc}")


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

app = App(app_ui, server)


def main():
    import shiny
    shiny.run_app(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
