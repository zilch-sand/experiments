"""LLM Classification App - Streamlit Frontend.

A local app for LLM-based text classification using Vertex AI.
Supports Google (Gemini), Anthropic (Claude), and Meta (Llama) models.
"""

import io
import json
import hashlib
from pathlib import Path

import pandas as pd
import streamlit as st

from backend.prompt import (
    PromptTemplate,
    DEFAULT_CLASSIFICATION_PROMPT,
    DEFAULT_MULTI_LABEL_PROMPT,
    FEEDBACK_PROMPT,
)
from backend.models import (
    get_available_models,
    get_model_by_display_name,
    create_model_config,
    THINKING_LEVELS,
    ModelConfig,
)
from backend.pricing import estimate_dataset_cost, format_cost, ModelPrice
from backend.fuzzy_match import find_safe_delimiter
from backend.classifier import (
    classify_rows,
    count_tokens_for_prompt,
    estimate_tokens_from_sample,
    apply_results_to_dataframe,
)
from backend.feedback import get_prompt_feedback
from backend.batch import (
    prepare_batch_requests,
    submit_batch,
    check_batch_status,
    retrieve_batch_results,
    load_tracked_batches,
    cleanup_batch,
)
from backend.arena import (
    run_arena,
    judge_arena_results,
    export_arena_data,
    DEFAULT_JUDGE_PROMPT,
)

st.set_page_config(page_title="LLM Classifier", layout="wide")


# ── Prompt caching helper ──────────────────────────────────────────────
def _prompt_cache_key(template: str, categories: list[str]) -> str:
    raw = template + "||" + "||".join(categories)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


# ── Session state defaults ─────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
if "results" not in st.session_state:
    st.session_state.results = None
if "arena_results" not in st.session_state:
    st.session_state.arena_results = None
if "prompt_cache" not in st.session_state:
    st.session_state.prompt_cache = {}


# ── Sidebar: Data Upload ───────────────────────────────────────────────
st.sidebar.title("📁 Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if uploaded_file is not None:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.sidebar.success(
        f"Loaded {len(st.session_state.df)} rows, "
        f"{len(st.session_state.df.columns)} columns"
    )

df = st.session_state.df

# ── Tabs ────────────────────────────────────────────────────────────────
tab_classify, tab_arena, tab_batch = st.tabs(
    ["🏷️ Classify", "🏟️ Arena", "📦 Batch Jobs"]
)


# =========================================================================
#  CLASSIFY TAB
# =========================================================================
with tab_classify:
    st.header("Text Classification")

    if df is None:
        st.info("⬆️ Upload a CSV file in the sidebar to get started.")
        st.stop()

    col_left, col_right = st.columns([1, 1])

    # ── Left column: Prompt & Categories ──────────────────────────────
    with col_left:
        st.subheader("Prompt Template")
        available_cols = list(df.columns)

        # Show available columns
        st.caption(
            "Available columns: " + ", ".join(f"`{{{c}}}`" for c in available_cols)
        )
        st.caption("Use `{label_options}` for the category list.")

        multi_label = st.checkbox("Multi-label classification", value=False)
        default_prompt = (
            DEFAULT_MULTI_LABEL_PROMPT if multi_label else DEFAULT_CLASSIFICATION_PROMPT
        )

        # Check prompt cache
        cache_key = _prompt_cache_key(
            st.session_state.get("_last_prompt", default_prompt),
            st.session_state.get("_last_categories", []),
        )

        prompt_text = st.text_area(
            "Prompt template",
            value=default_prompt,
            height=200,
            key="prompt_input",
        )

        prompt_template = PromptTemplate(prompt_text)

        # Validate
        errors = prompt_template.validate(available_cols)
        warnings = prompt_template.check_warnings(available_cols)

        for w in warnings:
            st.warning(w)
        for e in errors:
            st.error(e)

        # Categories
        st.subheader("Categories")
        categories_text = st.text_area(
            "Enter categories (one per line)",
            value="Category A\nCategory B\nCategory C",
            height=150,
            key="categories_input",
        )
        categories = [c.strip() for c in categories_text.strip().split("\n") if c.strip()]

        if multi_label:
            delimiter = find_safe_delimiter(categories)
            st.caption(f"Multi-label delimiter: `{delimiter}`")

        # Prompt preview
        st.subheader("Prompt Preview (Row 1)")
        if not errors and len(df) > 0:
            preview = prompt_template.preview(
                df.iloc[0].to_dict(),
                categories,
                multi_label,
                delimiter if multi_label else "|",
            )
            st.code(preview, language="text")

            # Cache prompt + categories
            st.session_state["_last_prompt"] = prompt_text
            st.session_state["_last_categories"] = categories
            st.session_state.prompt_cache[
                _prompt_cache_key(prompt_text, categories)
            ] = {"prompt": prompt_text, "categories": categories}

    # ── Right column: Model Selection & Run ───────────────────────────
    with col_right:
        st.subheader("Model Selection")
        models = get_available_models()
        model_names = [f"{m['name']} ({m['vendor']})" for m in models]

        selected_model_name = st.selectbox("Model", model_names, key="classify_model")
        selected_model = get_model_by_display_name(selected_model_name)

        if selected_model:
            vendor = selected_model["vendor"]
            thinking_options = THINKING_LEVELS.get(vendor, [])

            temperature = st.slider(
                "Temperature", 0.0, 1.0, 0.0, 0.1, key="classify_temp"
            )

            thinking_level = None
            if thinking_options:
                thinking_level = st.select_slider(
                    "Thinking level",
                    options=thinking_options,
                    value="none",
                    key="classify_thinking",
                )

            model_config = create_model_config(
                selected_model,
                temperature=temperature,
                thinking_level=thinking_level,
            )

            # Token estimation
            st.subheader("Cost Estimate")
            if not errors and categories:
                token_info = estimate_tokens_from_sample(
                    df, prompt_template, categories,
                    model_config.model_id, sample_size=5,
                )
                avg_in = token_info["avg_input_tokens"]
                # Rough output estimate for classification
                avg_out = 20  # classifications are short

                st.metric("Avg input tokens/row", f"{avg_in:.0f}")
                st.metric("Total rows", len(df))

                if selected_model.get("price"):
                    price = selected_model["price"]
                    full_cost = estimate_dataset_cost(
                        price, avg_in, avg_out, len(df)
                    )
                    st.metric("Estimated total cost", format_cost(full_cost))

                    if price.input_cached_per_mtok is not None:
                        cached_cost = estimate_dataset_cost(
                            price, avg_in, avg_out, len(df),
                            cached_input_tokens=int(avg_in * 0.8),
                        )
                        st.caption(
                            f"With prompt caching (~80%): {format_cost(cached_cost)}"
                        )

        # ── AI Feedback Button ─────────────────────────────────────────
        st.subheader("Prompt Feedback")
        if st.button("🤖 Get AI Feedback on Prompt & Categories", key="feedback_btn"):
            if not categories:
                st.warning("Add categories first.")
            elif not selected_model:
                st.warning("Select a model first.")
            else:
                with st.spinner("Getting AI feedback..."):
                    try:
                        feedback = get_prompt_feedback(
                            model_config, prompt_text, categories, multi_label
                        )
                        st.markdown(feedback)
                    except Exception as e:
                        st.error(f"Feedback error: {e}")

        # ── Test Run ───────────────────────────────────────────────────
        st.subheader("Test Classification")
        test_rows = st.number_input(
            "Number of rows to test", min_value=1, max_value=50, value=5,
            key="test_rows",
        )

        if st.button("▶️ Run Test", key="run_test_btn"):
            if errors:
                st.error("Fix prompt errors before running.")
            elif not categories:
                st.error("Add categories first.")
            else:
                progress_bar = st.progress(0, text="Classifying...")

                def update_progress(current, total):
                    progress_bar.progress(
                        current / total, text=f"Row {current}/{total}"
                    )

                try:
                    results = classify_rows(
                        df=df,
                        model_config=model_config,
                        prompt_template=prompt_template,
                        categories=categories,
                        multi_label=multi_label,
                        delimiter=delimiter if multi_label else "|",
                        max_rows=test_rows,
                        progress_callback=update_progress,
                    )
                    st.session_state.results = results
                    progress_bar.progress(1.0, text="Complete!")

                    # Display results
                    result_df = apply_results_to_dataframe(
                        df.head(test_rows),
                        results,
                        multi_label=multi_label,
                        delimiter=delimiter if multi_label else "|",
                    )

                    # Show only prompt columns + classification
                    display_cols = (
                        prompt_template.columns_used
                        + ["classification", "raw_response"]
                    )
                    display_cols = [c for c in display_cols if c in result_df.columns]
                    st.dataframe(result_df[display_cols], use_container_width=True)

                    # Token stats
                    total_in = sum(r.input_tokens for r in results)
                    total_out = sum(r.output_tokens for r in results)
                    avg_in = total_in / len(results) if results else 0
                    avg_out = total_out / len(results) if results else 0

                    st.caption(
                        f"Tokens — avg input: {avg_in:.0f}, avg output: {avg_out:.0f}"
                    )

                    if selected_model.get("price"):
                        sample_cost = selected_model["price"].estimate_cost(
                            total_in, total_out
                        )
                        full_cost = estimate_dataset_cost(
                            selected_model["price"], avg_in, avg_out, len(df)
                        )
                        st.caption(
                            f"Sample cost: {format_cost(sample_cost)} | "
                            f"Estimated full dataset: {format_cost(full_cost)}"
                        )

                except Exception as e:
                    st.error(f"Classification error: {e}")

        # ── Save Results ───────────────────────────────────────────────
        st.subheader("Save Results")
        if st.button("💾 Classify Full Dataset & Save", key="save_btn"):
            if errors:
                st.error("Fix prompt errors first.")
            elif not categories:
                st.error("Add categories first.")
            else:
                st.warning(
                    "⚠️ For large datasets, consider using Batch Jobs tab instead."
                )
                progress_bar = st.progress(0, text="Classifying full dataset...")

                def update_full_progress(current, total):
                    progress_bar.progress(
                        current / total, text=f"Row {current}/{total}"
                    )

                try:
                    results = classify_rows(
                        df=df,
                        model_config=model_config,
                        prompt_template=prompt_template,
                        categories=categories,
                        multi_label=multi_label,
                        delimiter=delimiter if multi_label else "|",
                        progress_callback=update_full_progress,
                    )
                    progress_bar.progress(1.0, text="Complete!")

                    result_df = apply_results_to_dataframe(
                        df, results, multi_label=multi_label,
                        delimiter=delimiter if multi_label else "|",
                    )

                    csv_buffer = io.BytesIO()
                    result_df.to_csv(csv_buffer, index=False)
                    st.download_button(
                        label="📥 Download Classified CSV",
                        data=csv_buffer.getvalue(),
                        file_name="classified_output.csv",
                        mime="text/csv",
                    )
                except Exception as e:
                    st.error(f"Error: {e}")


# =========================================================================
#  ARENA TAB
# =========================================================================
with tab_arena:
    st.header("🏟️ Model Arena")

    if df is None:
        st.info("⬆️ Upload a CSV file in the sidebar to get started.")
    else:
        arena_left, arena_right = st.columns([1, 1])

        with arena_left:
            st.subheader("Arena Configuration")

            # Reuse prompt & categories from classify tab
            arena_prompt_text = st.text_area(
                "Prompt template",
                value=st.session_state.get("prompt_input", DEFAULT_CLASSIFICATION_PROMPT),
                height=150,
                key="arena_prompt",
            )
            arena_template = PromptTemplate(arena_prompt_text)

            arena_multi_label = st.checkbox(
                "Multi-label", value=False, key="arena_multi"
            )
            arena_categories_text = st.text_area(
                "Categories (one per line)",
                value=st.session_state.get(
                    "categories_input", "Category A\nCategory B\nCategory C"
                ),
                height=100,
                key="arena_categories",
            )
            arena_categories = [
                c.strip()
                for c in arena_categories_text.strip().split("\n")
                if c.strip()
            ]
            arena_delimiter = (
                find_safe_delimiter(arena_categories) if arena_multi_label else "|"
            )

            arena_rows = st.number_input(
                "Rows to compare", min_value=1, max_value=50, value=5,
                key="arena_rows",
            )

        with arena_right:
            st.subheader("Select Models")
            models = get_available_models()
            model_names = [f"{m['name']} ({m['vendor']})" for m in models]

            # Allow selecting multiple models (or same model with different params)
            num_models = st.number_input(
                "Number of model configurations",
                min_value=2, max_value=6, value=2, key="num_arena_models",
            )

            arena_configs = []
            for i in range(num_models):
                st.markdown(f"**Model {i + 1}**")
                col_m, col_t, col_th = st.columns([2, 1, 1])

                with col_m:
                    sel = st.selectbox(
                        "Model", model_names, key=f"arena_model_{i}"
                    )
                with col_t:
                    temp = st.slider(
                        "Temp", 0.0, 1.0, 0.0, 0.1, key=f"arena_temp_{i}"
                    )
                with col_th:
                    model_info = get_model_by_display_name(sel)
                    vendor = model_info["vendor"] if model_info else ""
                    t_options = THINKING_LEVELS.get(vendor, [])
                    think = None
                    if t_options:
                        think = st.select_slider(
                            "Think",
                            options=t_options,
                            value="none",
                            key=f"arena_think_{i}",
                        )

                if model_info:
                    config = create_model_config(
                        model_info, temperature=temp, thinking_level=think
                    )
                    arena_configs.append(config)

            # Cost estimates
            st.subheader("Price Estimates (full dataset)")
            for config in arena_configs:
                if config.price:
                    # Use rough token estimate
                    token_info = estimate_tokens_from_sample(
                        df, arena_template, arena_categories,
                        config.model_id, sample_size=3,
                    )
                    avg_in = token_info["avg_input_tokens"]
                    avg_out = 20
                    cost = estimate_dataset_cost(
                        config.price, avg_in, avg_out, len(df)
                    )
                    st.caption(
                        f"{config.display_name}: {format_cost(cost)}"
                    )

        # ── Run Arena ─────────────────────────────────────────────────
        if st.button("🏁 Run Arena Comparison", key="run_arena_btn"):
            if len(arena_configs) < 2:
                st.error("Select at least 2 models.")
            elif not arena_categories:
                st.error("Add categories.")
            else:
                arena_progress = st.progress(0, text="Running arena...")

                try:
                    arena_data = run_arena(
                        df=df,
                        model_configs=arena_configs,
                        prompt_template=arena_template,
                        categories=arena_categories,
                        multi_label=arena_multi_label,
                        delimiter=arena_delimiter,
                        max_rows=arena_rows,
                        progress_callback=lambda p: arena_progress.progress(
                            p, text=f"Progress: {p:.0%}"
                        ),
                    )
                    st.session_state.arena_results = arena_data
                    arena_progress.progress(1.0, text="Complete!")
                except Exception as e:
                    st.error(f"Arena error: {e}")

        # ── Display Arena Results ─────────────────────────────────────
        if st.session_state.arena_results:
            arena_data = st.session_state.arena_results
            st.subheader("Results Comparison")

            export_df = export_arena_data(
                arena_data, df, arena_template, arena_rows
            )
            st.dataframe(export_df, use_container_width=True)

            # Token stats table
            st.subheader("Token & Cost Statistics")
            stats_rows = []
            for model_key, stats in arena_data["token_stats"].items():
                stats_rows.append({
                    "Model": model_key,
                    "Avg Input Tokens": f"{stats['avg_input_tokens']:.0f}",
                    "Avg Output Tokens": f"{stats['avg_output_tokens']:.0f}",
                    "Sample Cost": format_cost(stats["sample_cost"]),
                    "Est. Full Dataset Cost": format_cost(
                        stats["estimated_full_cost"]
                    ),
                })
            st.table(pd.DataFrame(stats_rows))

            # ── Judge ─────────────────────────────────────────────────
            st.subheader("🧑‍⚖️ Judge Evaluation")

            judge_col1, judge_col2 = st.columns([1, 1])
            with judge_col1:
                judge_model_name = st.selectbox(
                    "Judge Model", model_names, key="judge_model"
                )
                judge_model_info = get_model_by_display_name(judge_model_name)

            with judge_col2:
                judge_prompt = st.text_area(
                    "Judge Prompt",
                    value=DEFAULT_JUDGE_PROMPT,
                    height=200,
                    key="judge_prompt_input",
                )

            if st.button("⚖️ Run Judge", key="run_judge_btn"):
                if judge_model_info:
                    judge_config = create_model_config(judge_model_info)
                    with st.spinner("Judge is evaluating..."):
                        try:
                            verdict = judge_arena_results(
                                arena_data, df, arena_template,
                                arena_categories, judge_config,
                                judge_prompt, arena_rows,
                            )
                            st.markdown(verdict)
                        except Exception as e:
                            st.error(f"Judge error: {e}")

            # ── Export ────────────────────────────────────────────────
            st.subheader("Export Arena Data")
            csv_buf = io.BytesIO()
            export_df.to_csv(csv_buf, index=False)
            st.download_button(
                label="📥 Download Arena CSV",
                data=csv_buf.getvalue(),
                file_name="arena_comparison.csv",
                mime="text/csv",
                key="export_arena_btn",
            )


# =========================================================================
#  BATCH JOBS TAB
# =========================================================================
with tab_batch:
    st.header("📦 Batch Processing")

    if df is None:
        st.info("⬆️ Upload a CSV file in the sidebar to get started.")
    else:
        batch_left, batch_right = st.columns([1, 1])

        with batch_left:
            st.subheader("Submit Batch Job")

            # Reuse prompt & categories
            batch_prompt_text = st.text_area(
                "Prompt template",
                value=st.session_state.get(
                    "prompt_input", DEFAULT_CLASSIFICATION_PROMPT
                ),
                height=150,
                key="batch_prompt",
            )
            batch_template = PromptTemplate(batch_prompt_text)

            batch_multi_label = st.checkbox(
                "Multi-label", value=False, key="batch_multi"
            )
            batch_categories_text = st.text_area(
                "Categories (one per line)",
                value=st.session_state.get(
                    "categories_input", "Category A\nCategory B\nCategory C"
                ),
                height=100,
                key="batch_categories",
            )
            batch_categories = [
                c.strip()
                for c in batch_categories_text.strip().split("\n")
                if c.strip()
            ]

            batch_model_name = st.selectbox(
                "Model", model_names if df is not None else [],
                key="batch_model",
            )
            batch_model_info = get_model_by_display_name(batch_model_name)

            batch_description = st.text_input(
                "Batch description", value="Classification batch",
                key="batch_desc",
            )

            if st.button("🚀 Submit Batch", key="submit_batch_btn"):
                if batch_model_info and batch_categories:
                    batch_config = create_model_config(batch_model_info)
                    batch_delimiter = (
                        find_safe_delimiter(batch_categories)
                        if batch_multi_label
                        else "|"
                    )
                    requests = prepare_batch_requests(
                        df, batch_config, batch_template,
                        batch_categories, batch_multi_label, batch_delimiter,
                    )

                    with st.spinner("Submitting batch..."):
                        try:
                            batch_id = submit_batch(
                                requests, batch_config, batch_description
                            )
                            st.success(f"Batch submitted! ID: `{batch_id}`")
                        except Exception as e:
                            st.error(f"Batch submission error: {e}")
                else:
                    st.warning("Select a model and add categories.")

        with batch_right:
            st.subheader("Tracked Batches")

            batches = load_tracked_batches()
            if not batches:
                st.info("No tracked batches.")
            else:
                for batch in batches:
                    bid = batch.get("batch_id", "unknown")
                    status = batch.get("status", "unknown")
                    created = batch.get("created_at", "?")

                    with st.expander(f"Batch `{bid[:12]}...` — {status}"):
                        st.json(batch)

                        col_check, col_get, col_clean = st.columns(3)
                        with col_check:
                            if st.button(
                                "🔄 Check Status", key=f"check_{bid}"
                            ):
                                result = check_batch_status(bid)
                                st.json(result)
                        with col_get:
                            if st.button(
                                "📥 Get Results", key=f"get_{bid}"
                            ):
                                # Use categories from batch tab input
                                cats = batch_categories
                                ml = batch.get("multi_label", False)
                                dlm = batch.get("delimiter", "|")
                                results = retrieve_batch_results(
                                    bid, cats, ml, dlm
                                )
                                if results and "error" not in results[0]:
                                    st.dataframe(
                                        pd.DataFrame(results),
                                        use_container_width=True,
                                    )
                                else:
                                    st.warning(
                                        f"Could not retrieve: {results}"
                                    )
                        with col_clean:
                            if st.button(
                                "🗑️ Cleanup", key=f"clean_{bid}"
                            ):
                                cleanup_batch(bid)
                                st.success("Cleaned up!")
                                st.rerun()
