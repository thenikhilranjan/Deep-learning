"""Streamlit dashboard for the Assessment 3 search-and-rescue project."""

from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import altair as alt
import cv2
import numpy as np
import pandas as pd
import streamlit as st

from sar_vision import get_settings
from sar_vision.data.manifest import load_manifest, sequence_rows
from sar_vision.data.models import DatasetReport
from sar_vision.data.validator import DatasetValidator
from sar_vision.inference.service import DetectionService, DetectorConfig
from sar_vision.preprocessing import PreprocessOptions, apply_preprocessing
from sar_vision.storage import DatabaseManager
from sar_vision.training import YoloTrainingManager
from sar_vision.ui import to_rgb


st.set_page_config(
    page_title="SAR Vision Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_db() -> DatabaseManager:
    database = DatabaseManager()
    database.initialize()
    return database


@st.cache_resource
def get_detector() -> DetectionService:
    return DetectionService()


@st.cache_data
def _load_manifest_cached(path: str, manifest_mtime: float) -> DatasetReport:
    del manifest_mtime
    return load_manifest(Path(path))


def inject_custom_css() -> None:
    """Apply the visual theme for the rescue dashboard."""
    st.markdown(
        """
        <style>
        :root {
            --sar-bg: #08111f;
            --sar-bg-soft: rgba(12, 24, 43, 0.85);
            --sar-panel: rgba(15, 26, 46, 0.86);
            --sar-panel-strong: rgba(20, 36, 63, 0.95);
            --sar-border: rgba(255, 255, 255, 0.08);
            --sar-text: #f5f8ff;
            --sar-muted: #9fb2cc;
            --sar-accent: #ff8f45;
            --sar-accent-strong: #ff5f6d;
            --sar-cool: #58d6b4;
            --sar-warn: #ffb347;
        }

        .stApp {
            background:
                radial-gradient(circle at 0% 0%, rgba(255, 143, 69, 0.18), transparent 28%),
                radial-gradient(circle at 100% 0%, rgba(88, 214, 180, 0.16), transparent 26%),
                linear-gradient(180deg, #08111f 0%, #0d1730 100%);
            color: var(--sar-text);
        }

        .main .block-container {
            max-width: 1380px;
            padding-top: 1.75rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0c1628 0%, #111d34 100%);
            border-right: 1px solid var(--sar-border);
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.2rem;
        }

        h1, h2, h3 {
            color: var(--sar-text);
            letter-spacing: -0.02em;
        }

        .rescue-hero {
            background:
                linear-gradient(135deg, rgba(255, 143, 69, 0.22), rgba(255, 95, 109, 0.1)),
                var(--sar-panel-strong);
            border: 1px solid var(--sar-border);
            border-radius: 28px;
            padding: 1.65rem 1.75rem;
            box-shadow: 0 24px 50px rgba(0, 0, 0, 0.28);
            margin-bottom: 1.1rem;
        }

        .rescue-kicker {
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.74rem;
            color: #ffd0a8;
            margin-bottom: 0.35rem;
        }

        .rescue-title {
            font-size: 2.4rem;
            font-weight: 700;
            margin: 0;
        }

        .rescue-copy {
            color: #d5dfed;
            font-size: 1rem;
            line-height: 1.65;
            max-width: 900px;
            margin-top: 0.65rem;
        }

        .metric-card {
            background: rgba(9, 18, 34, 0.82);
            border: 1px solid var(--sar-border);
            border-radius: 22px;
            padding: 1.05rem 1.15rem;
            min-height: 132px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.16);
            margin-bottom: 0.8rem;
        }

        .metric-card.warm {
            border-color: rgba(255, 143, 69, 0.22);
        }

        .metric-card.cool {
            border-color: rgba(88, 214, 180, 0.22);
        }

        .metric-card.hot {
            border-color: rgba(255, 95, 109, 0.22);
        }

        .metric-label {
            color: var(--sar-muted);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }

        .metric-value {
            color: var(--sar-text);
            font-size: 2.05rem;
            font-weight: 700;
            margin: 0.35rem 0 0.2rem;
        }

        .metric-foot {
            color: #d3dceb;
            font-size: 0.92rem;
            line-height: 1.45;
        }

        .panel-shell {
            background: var(--sar-panel);
            border: 1px solid var(--sar-border);
            border-radius: 22px;
            padding: 1.1rem 1.2rem;
            margin-bottom: 1rem;
        }

        .panel-title {
            font-size: 1.08rem;
            font-weight: 600;
            color: var(--sar-text);
            margin-bottom: 0.25rem;
        }

        .panel-copy {
            color: #c6d3e5;
            line-height: 1.58;
            margin-bottom: 0;
        }

        .issue-card {
            border-radius: 18px;
            padding: 1rem 1.1rem;
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 0.7rem;
        }

        .issue-card.warn {
            background: rgba(255, 179, 71, 0.12);
            border-color: rgba(255, 179, 71, 0.2);
        }

        .issue-card.hot {
            background: rgba(255, 95, 109, 0.12);
            border-color: rgba(255, 95, 109, 0.2);
        }

        .issue-card.cool {
            background: rgba(88, 214, 180, 0.1);
            border-color: rgba(88, 214, 180, 0.18);
        }

        .issue-title {
            color: var(--sar-text);
            font-weight: 600;
            margin-bottom: 0.25rem;
        }

        .issue-copy {
            color: #d8e1ee;
            line-height: 1.5;
            font-size: 0.94rem;
        }

        .sidebar-card {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            margin-bottom: 1rem;
        }

        .sidebar-title {
            color: var(--sar-text);
            font-weight: 600;
            margin-bottom: 0.3rem;
        }

        .sidebar-copy {
            color: var(--sar-muted);
            line-height: 1.5;
            font-size: 0.92rem;
        }

        .stButton > button, .stDownloadButton > button {
            background: linear-gradient(135deg, #ff8f45 0%, #ff5f6d 100%);
            color: white;
            border: none;
            border-radius: 999px;
            padding: 0.65rem 1.15rem;
            font-weight: 600;
            box-shadow: 0 12px 22px rgba(255, 95, 109, 0.2);
        }

        .stButton > button:hover, .stDownloadButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 16px 30px rgba(255, 95, 109, 0.28);
        }

        .stFileUploader > div {
            background: rgba(255, 255, 255, 0.03);
            border: 1px dashed rgba(255, 255, 255, 0.16);
            border-radius: 18px;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--sar-border);
            border-radius: 18px;
            overflow: hidden;
            background: rgba(9, 16, 29, 0.7);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 0.5rem 0.95rem;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--sar-border);
        }

        .stTabs [aria-selected="true"] {
            background: rgba(255, 143, 69, 0.16);
            border-color: rgba(255, 143, 69, 0.32);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_number(value: int) -> str:
    """Format integer values with separators."""
    return f"{value:,}"


def build_metric_card(label: str, value: str, foot: str, tone: str = "warm") -> str:
    """Return a styled HTML metric card."""
    return f"""
    <div class="metric-card {tone}">
        <div class="metric-label">{html.escape(label)}</div>
        <div class="metric-value">{html.escape(value)}</div>
        <div class="metric-foot">{html.escape(foot)}</div>
    </div>
    """


def render_metric_cards(cards: List[Dict[str, str]]) -> None:
    """Render metric cards in a responsive row."""
    columns = st.columns(len(cards))
    for column, card in zip(columns, cards):
        column.markdown(
            build_metric_card(
                card["label"],
                card["value"],
                card["foot"],
                card.get("tone", "warm"),
            ),
            unsafe_allow_html=True,
        )


def render_panel(title: str, body: str) -> None:
    """Render a styled information panel."""
    st.markdown(
        f"""
        <div class="panel-shell">
            <div class="panel-title">{html.escape(title)}</div>
            <div class="panel-copy">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_issue_cards(issues: List[str]) -> None:
    """Display dataset issues with stronger visual hierarchy."""
    if not issues:
        st.markdown(
            """
            <div class="issue-card cool">
                <div class="issue-title">Dataset health check</div>
                <div class="issue-copy">No blocking issues were found during validation.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for issue in issues:
        tone = "warn"
        if "no image" in issue.lower() or "missing" in issue.lower():
            tone = "hot"
        st.markdown(
            f"""
            <div class="issue-card {tone}">
                <div class="issue-title">Attention point</div>
                <div class="issue-copy">{html.escape(issue)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def image_to_png_bytes(image: np.ndarray) -> bytes:
    """Encode an image array to PNG bytes for download/export."""
    success, encoded = cv2.imencode(".png", image)
    if not success:
        raise ValueError("Could not encode image to PNG.")
    return encoded.tobytes()


def dataframe_to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    """Encode a dataframe to CSV bytes."""
    return dataframe.to_csv(index=False).encode("utf-8")


def build_bar_chart(
    dataframe: pd.DataFrame,
    *,
    x: str,
    y: str,
    color: str,
    title: str,
    height: int = 320,
) -> alt.Chart:
    """Build a styled Altair bar chart."""
    return (
        alt.Chart(dataframe)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X(x, title=None),
            y=alt.Y(y, title=title),
            color=alt.Color(
                color,
                scale=alt.Scale(
                    range=["#ff8f45", "#58d6b4", "#ff5f6d", "#ffb347", "#9fb2cc"]
                ),
            ),
            tooltip=list(dataframe.columns),
        )
        .properties(height=height)
        .configure_view(strokeOpacity=0)
    )


def build_line_chart(
    dataframe: pd.DataFrame,
    *,
    x: str,
    y: str,
    color: str,
    title: str,
    height: int = 320,
) -> alt.Chart:
    """Build a styled Altair line chart."""
    return (
        alt.Chart(dataframe)
        .mark_line(strokeWidth=2.5)
        .encode(
            x=alt.X(x, title=None),
            y=alt.Y(y, title=title),
            color=alt.Color(
                color,
                scale=alt.Scale(range=["#58d6b4", "#ff8f45"]),
            ),
            tooltip=list(dataframe.columns),
        )
        .properties(height=height)
        .configure_view(strokeOpacity=0)
    )


def load_dataset_report(force_refresh: bool = False) -> DatasetReport:
    """Load or regenerate the dataset manifest."""
    settings = get_settings()
    validator = DatasetValidator()
    database = get_db()

    if force_refresh or not settings.dataset_manifest_path.exists():
        report = validator.validate(write_outputs=True)
        database.log_dataset_report(
            {
                "generated_at": report.generated_at,
                "dataset_root": report.dataset_root,
                "sequence_count": report.sequence_count,
                "image_count": report.image_count,
                "label_count": report.label_count,
                "matched_pairs": report.matched_pairs,
                "missing_images": report.missing_images,
                "missing_labels": report.missing_labels,
                "issues": report.issues,
            }
        )
        st.cache_data.clear()
        return report

    manifest_mtime = settings.dataset_manifest_path.stat().st_mtime
    return _load_manifest_cached(str(settings.dataset_manifest_path), manifest_mtime)


def load_image_from_path(path: Path) -> np.ndarray:
    """Load an image from disk using OpenCV."""
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"Could not read image from {path}")
    return image


def load_uploaded_image(file_data) -> Tuple[np.ndarray, str]:
    """Load an uploaded image without consuming the file buffer permanently."""
    buffer = np.frombuffer(file_data.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("Could not decode uploaded image.")
    return image, file_data.name


def dataset_health_metrics(report: DatasetReport) -> Dict[str, float]:
    """Compute summary metrics used across pages."""
    sequence_df = pd.DataFrame(sequence_rows(report))
    matched_label_rate = (
        (report.matched_pairs / report.label_count) * 100 if report.label_count else 0.0
    )
    labeled_image_rate = (
        ((report.image_count - report.missing_labels) / report.image_count) * 100
        if report.image_count
        else 0.0
    )
    clean_sequences = 0
    if not sequence_df.empty:
        clean_sequences = int((sequence_df["missing_images"] == 0).sum())
    return {
        "matched_label_rate": matched_label_rate,
        "labeled_image_rate": labeled_image_rate,
        "clean_sequences": clean_sequences,
    }


def dataset_image_selector(
    report: DatasetReport, *, widget_prefix: str
) -> Tuple[Optional[np.ndarray], Optional[str], str, str]:
    """Select an image from the dataset, sample assets, or an upload."""
    source_type = st.radio(
        "Image source",
        options=("Dataset sample", "Sample asset", "Upload image"),
        horizontal=True,
        key=f"{widget_prefix}_source_type",
    )

    if source_type == "Upload image":
        uploaded = st.file_uploader(
            "Upload an image",
            type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"],
            key=f"{widget_prefix}_upload",
        )
        if uploaded is None:
            return None, None, "unknown", source_type
        image, name = load_uploaded_image(uploaded)
        return image, name, "unknown", source_type

    if source_type == "Sample asset":
        settings = get_settings()
        assets = sorted((settings.project_root / "assets" / "samples").glob("*"))
        if not assets:
            st.info("No sample assets are available yet.")
            return None, None, "unknown", source_type
        selected_asset = st.selectbox(
            "Select sample asset",
            options=assets,
            format_func=lambda path: path.name,
            key=f"{widget_prefix}_asset",
        )
        return load_image_from_path(selected_asset), str(selected_asset), "unknown", source_type

    samples = [sample for sample in report.samples if sample.image_exists and sample.image_path]
    if not samples:
        st.warning("The manifest currently has no usable image samples.")
        return None, None, "unknown", source_type

    available_modalities = sorted({sample.modality for sample in samples})
    selected_modality = st.selectbox(
        "Dataset modality",
        options=available_modalities,
        key=f"{widget_prefix}_modality",
    )
    modality_samples = [sample for sample in samples if sample.modality == selected_modality]
    sequences = sorted({sample.sequence_name for sample in modality_samples})

    selected_sequence = st.selectbox(
        "Select sequence",
        options=sequences,
        key=f"{widget_prefix}_sequence",
    )
    sequence_samples = [
        sample for sample in modality_samples if sample.sequence_name == selected_sequence
    ]
    selected_index = st.number_input(
        "Sample index",
        min_value=0,
        max_value=max(len(sequence_samples) - 1, 0),
        value=0,
        step=1,
        key=f"{widget_prefix}_sample_index",
    )
    selected_sample = sequence_samples[int(selected_index)]
    st.caption(f"Selected file: {Path(selected_sample.image_path or '').name}")
    return (
        load_image_from_path(Path(selected_sample.image_path or "")),
        selected_sample.image_path,
        selected_sample.modality,
        source_type,
    )


def preprocessing_controls(prefix: str) -> PreprocessOptions:
    """Render preprocessing controls with clearer help text."""
    normalize_thermal = st.checkbox(
        "Thermal normalization",
        value=True,
        help="Stretch thermal intensities to make hotspots easier to separate.",
        key=f"{prefix}_normalize_thermal",
    )
    apply_clahe = st.checkbox(
        "CLAHE contrast enhancement",
        help="Improve local contrast in dark or low-texture frames.",
        key=f"{prefix}_clahe",
    )
    denoise = st.checkbox(
        "Denoise",
        help="Reduce sensor noise before detection or visualization.",
        key=f"{prefix}_denoise",
    )
    denoise_method = st.selectbox(
        "Denoise method",
        options=("gaussian", "median", "bilateral"),
        index=0,
        key=f"{prefix}_denoise_method",
        disabled=not denoise,
        help="Choose the denoising strategy after enabling Denoise.",
    )
    grayscale = st.checkbox(
        "Force grayscale output",
        help="Useful for thermal-only or histogram-based analysis.",
        key=f"{prefix}_grayscale",
    )
    resize_enabled = st.checkbox(
        "Resize to 640 x 640",
        help="Match a common detector input size for faster experimentation.",
        key=f"{prefix}_resize",
    )
    resize_to = (640, 640) if resize_enabled else None

    if not denoise:
        st.caption("Enable Denoise to choose a filtering method.")

    return PreprocessOptions(
        normalize_thermal=normalize_thermal,
        apply_clahe=apply_clahe,
        denoise=denoise,
        denoise_method=denoise_method,
        resize_to=resize_to,
        grayscale=grayscale,
    )


def render_sidebar_context(report: DatasetReport) -> None:
    """Render a polished mission summary in the sidebar."""
    settings = get_settings()
    health = dataset_health_metrics(report)
    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-title">Mission Console</div>
            <div class="sidebar-copy">
                Dataset validation, preprocessing, inference, and experiment logging
                for the Assignment 3 search-and-rescue workflow.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Project root: `{settings.project_root}`")
    st.caption(f"Database: `{settings.db_path}`")
    st.caption(
        f"Matched label rate: {health['matched_label_rate']:.1f}% | "
        f"Clean sequences: {health['clean_sequences']}"
    )


def render_overview(report: DatasetReport) -> None:
    """Render the high-level project overview."""
    health = dataset_health_metrics(report)
    st.markdown(
        """
        <div class="rescue-hero">
            <div class="rescue-kicker">Assessment 3 Search and Rescue System</div>
            <h1 class="rescue-title">Drone-Assisted Wilderness Human Detection Dashboard</h1>
            <div class="rescue-copy">
                This interface validates local WiSARD data, previews image enhancement,
                prepares YOLO datasets, runs demo inference, and logs results in SQLite.
                It is aligned with the assignment goal of combining dataset handling,
                preprocessing, model comparison, and a practical operator-facing GUI.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_metric_cards(
        [
            {
                "label": "Sequences",
                "value": format_number(report.sequence_count),
                "foot": "Distinct local WiSARD sequence folders detected",
                "tone": "warm",
            },
            {
                "label": "Images",
                "value": format_number(report.image_count),
                "foot": f"{health['labeled_image_rate']:.1f}% of images currently have labels",
                "tone": "cool",
            },
            {
                "label": "Labels",
                "value": format_number(report.label_count),
                "foot": f"{health['matched_label_rate']:.1f}% of labels align to local images",
                "tone": "warm",
            },
            {
                "label": "Matched pairs",
                "value": format_number(report.matched_pairs),
                "foot": f"{format_number(health['clean_sequences'])} clean sequences ready for experiments",
                "tone": "hot",
            },
        ]
    )

    left_column, right_column = st.columns([1.05, 1.15])
    with left_column:
        render_panel(
            "Assignment alignment",
            """
            <ul>
                <li>Dataset validation and manifest generation are implemented.</li>
                <li>Preprocessing supports thermal normalization, CLAHE, denoising, and resizing.</li>
                <li>Inference demo supports immediate classical detection and optional YOLO weights.</li>
                <li>SQLite logging stores dataset reports and run history for later reporting.</li>
                <li>YOLO workspace preparation is available from the Dataset Status page.</li>
            </ul>
            """,
        )
        render_panel(
            "Recommended operator flow",
            """
            1. Refresh the dataset manifest after any data changes.<br>
            2. Validate enhancement settings in the Preprocessing Lab.<br>
            3. Build a YOLO workspace for thermal or RGB baselines.<br>
            4. Use the Inference Demo for quick visual checks and export annotated results.
            """,
        )

    with right_column:
        st.subheader("Modality coverage")
        sequence_df = pd.DataFrame(sequence_rows(report))
        if sequence_df.empty:
            st.info("No sequence summary data is available yet.")
        else:
            modality_chart = (
                sequence_df.groupby("modality")[["image_count", "label_count", "matched_pairs"]]
                .sum()
                .reset_index()
                .melt(id_vars="modality", var_name="metric", value_name="count")
            )
            st.altair_chart(
                build_bar_chart(
                    modality_chart,
                    x="modality:N",
                    y="count:Q",
                    color="metric:N",
                    title="Count",
                ),
                use_container_width=True,
            )

    st.subheader("Current dataset issues")
    render_issue_cards(report.issues)


def render_dataset_status(report: DatasetReport) -> None:
    """Render the dataset validation page."""
    st.header("Dataset Status")
    st.caption(f"Manifest path: `{get_settings().dataset_manifest_path}`")

    if st.button("Refresh dataset manifest", type="primary"):
        with st.spinner("Refreshing local WiSARD manifest and summary..."):
            refreshed = load_dataset_report(force_refresh=True)
        st.success(
            f"Dataset refreshed. Found {format_number(refreshed.image_count)} images and "
            f"{format_number(refreshed.label_count)} labels."
        )
        report = refreshed

    health = dataset_health_metrics(report)
    render_metric_cards(
        [
            {
                "label": "Matched label rate",
                "value": f"{health['matched_label_rate']:.1f}%",
                "foot": "Local label files with matching image files",
                "tone": "cool",
            },
            {
                "label": "Images without labels",
                "value": format_number(report.missing_labels),
                "foot": "Potential background frames or missing annotations",
                "tone": "warn",
            },
            {
                "label": "Labels without images",
                "value": format_number(report.missing_images),
                "foot": "Needs review before final training runs",
                "tone": "hot",
            },
        ]
    )

    sequence_df = pd.DataFrame(sequence_rows(report))
    if not sequence_df.empty:
        sequence_df["status"] = np.where(
            sequence_df["missing_images"] > 0,
            "needs_image_review",
            np.where(sequence_df["missing_labels"] > 0, "partial_labels", "ready"),
        )
        modality_filter = st.multiselect(
            "Filter sequences by modality",
            options=sorted(sequence_df["modality"].unique()),
            default=sorted(sequence_df["modality"].unique()),
        )
        status_filter = st.multiselect(
            "Filter sequences by health state",
            options=sorted(sequence_df["status"].unique()),
            default=sorted(sequence_df["status"].unique()),
        )

        filtered_df = sequence_df[
            sequence_df["modality"].isin(modality_filter)
            & sequence_df["status"].isin(status_filter)
        ].sort_values(
            ["missing_images", "missing_labels", "matched_pairs"],
            ascending=[False, False, False],
        )

        chart_col, summary_col = st.columns([1.4, 1])
        with chart_col:
            st.subheader("Sequence breakdown")
            sequence_breakdown = (
                filtered_df.groupby(["modality", "status"]).size().unstack(fill_value=0)
            ).reset_index().melt(
                id_vars="modality", var_name="status", value_name="sequence_count"
            )
            st.altair_chart(
                build_bar_chart(
                    sequence_breakdown,
                    x="modality:N",
                    y="sequence_count:Q",
                    color="status:N",
                    title="Sequences",
                ),
                use_container_width=True,
            )

        with summary_col:
            render_panel(
                "Validation summary",
                (
                    f"Sequences in view: {format_number(len(filtered_df))}<br>"
                    f"Ready sequences: {format_number(int((filtered_df['status'] == 'ready').sum()))}<br>"
                    f"Needs image review: {format_number(int((filtered_df['status'] == 'needs_image_review').sum()))}"
                ),
            )

        st.dataframe(filtered_df, use_container_width=True, height=420)
        st.download_button(
            "Download sequence summary CSV",
            data=dataframe_to_csv_bytes(filtered_df),
            file_name="sequence_summary.csv",
            mime="text/csv",
        )
    else:
        st.warning("No sequence summaries are available yet.")

    with st.expander("Prepare YOLO dataset workspace"):
        st.caption(
            "This builds a train/val/test workspace from the validated manifest so that "
            "Ultralytics YOLO can train directly on the local dataset."
        )
        modality = st.selectbox("Modality", options=("thermal", "rgb", "all"))
        use_symlinks = st.checkbox("Use symlinks", value=True)
        if st.button("Build YOLO workspace"):
            try:
                with st.spinner("Preparing YOLO workspace from the dataset manifest..."):
                    manager = YoloTrainingManager()
                    data_yaml = manager.prepare_dataset(
                        modality=modality,
                        use_symlinks=use_symlinks,
                    )
                st.success(f"YOLO workspace created at `{data_yaml.parent}`")
                st.code(data_yaml.read_text(encoding="utf-8"))
            except Exception as exc:
                st.error(f"Could not prepare the YOLO workspace: {exc}")


def render_preprocessing_lab(report: DatasetReport) -> None:
    """Render the preprocessing preview page."""
    st.header("Preprocessing Lab")
    st.caption(
        "Compare original and enhanced frames before training or inference. "
        "This page supports the assignment requirement for explicit image processing."
    )

    left_column, right_column = st.columns([1, 2])
    with left_column:
        image, source_name, inferred_modality, source_type = dataset_image_selector(
            report, widget_prefix="preprocess"
        )
        options = preprocessing_controls("preprocess")

    if image is None:
        right_column.info("Choose an image source to preview preprocessing.")
        return

    processed, steps = apply_preprocessing(image, options)
    render_metric_cards(
        [
            {
                "label": "Source type",
                "value": source_type,
                "foot": "Current image feed used in the lab",
                "tone": "cool",
            },
            {
                "label": "Detected modality",
                "value": inferred_modality,
                "foot": "Derived from dataset naming or current selection",
                "tone": "warm",
            },
            {
                "label": "Processing steps",
                "value": str(len(steps)),
                "foot": ", ".join(steps) if steps else "No preprocessing applied",
                "tone": "hot",
            },
        ]
    )

    comparison_tab, histogram_tab = st.tabs(["Visual compare", "Intensity profile"])
    with comparison_tab:
        original_col, processed_col = st.columns(2)
        original_col.image(
            to_rgb(image), caption=f"Original: {source_name}", use_container_width=True
        )
        processed_col.image(
            to_rgb(processed),
            caption=f"Processed ({inferred_modality})",
            use_container_width=True,
        )
        st.download_button(
            "Download processed image",
            data=image_to_png_bytes(processed),
            file_name="processed_preview.png",
            mime="image/png",
        )

    with histogram_tab:
        original_gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        processed_gray = (
            processed if processed.ndim == 2 else cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        )
        histogram_df = pd.DataFrame(
            {
                "intensity": np.arange(256),
                "original": cv2.calcHist([original_gray], [0], None, [256], [0, 256]).flatten(),
                "processed": cv2.calcHist([processed_gray], [0], None, [256], [0, 256]).flatten(),
            }
        ).melt(id_vars="intensity", var_name="stage", value_name="count")
        st.altair_chart(
            build_line_chart(
                histogram_df,
                x="intensity:Q",
                y="count:Q",
                color="stage:N",
                title="Pixel count",
            ),
            use_container_width=True,
        )


def render_inference_demo(report: DatasetReport) -> None:
    """Render the inference demo page with export actions."""
    st.header("Inference Demo")
    st.caption(
        "Run a quick visual detection pass for assignment demos. The dashboard can use a "
        "classical thermal hotspot detector immediately or switch to YOLO weights when available."
    )

    left_column, right_column = st.columns([1, 2])
    with left_column:
        image, source_name, inferred_modality, _ = dataset_image_selector(
            report, widget_prefix="inference"
        )
        modality = st.selectbox(
            "Detection modality",
            options=("thermal", "rgb", "unknown"),
            index=("thermal", "rgb", "unknown").index(
                inferred_modality if inferred_modality in {"thermal", "rgb"} else "thermal"
            ),
        )
        backend = st.selectbox("Backend", options=("auto", "yolo", "thermal_hotspot"))
        confidence_threshold = st.slider(
            "Confidence threshold",
            min_value=0.05,
            max_value=0.95,
            value=0.25,
            step=0.05,
        )
        min_area_ratio = st.slider(
            "Minimum hotspot area ratio",
            min_value=0.0001,
            max_value=0.01,
            value=0.0005,
            step=0.0001,
        )
        options = preprocessing_controls("inference")

        model_options = sorted(get_settings().models_dir.rglob("*.pt"))
        selected_model = None
        if backend in {"auto", "yolo"} and model_options:
            selected_model = st.selectbox(
                "YOLO weights",
                options=model_options,
                format_func=lambda path: path.name,
            )
        elif backend in {"auto", "yolo"}:
            st.caption("No `.pt` model weights found in `artifacts/models` yet.")

        run_button = st.button("Run detection", type="primary")
        request_signature = {
            "source_name": source_name,
            "modality": modality,
            "backend": backend,
            "confidence_threshold": confidence_threshold,
            "min_area_ratio": min_area_ratio,
            "model_path": str(selected_model) if selected_model else None,
            "options": options.__dict__.copy(),
        }

    if image is None:
        right_column.info("Choose an image source to run detection.")
        return

    if run_button:
        with st.spinner("Running detection and logging the result..."):
            detector = get_detector()
            result = detector.run(
                image,
                modality=modality,
                preprocess_options=options,
                detector_config=DetectorConfig(
                    backend=backend,
                    model_path=selected_model,
                    confidence_threshold=confidence_threshold,
                    min_area_ratio=min_area_ratio,
                ),
            )
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = get_settings().exports_dir / f"inference_{timestamp}.png"
            cv2.imwrite(str(output_path), result["annotated_image"])

            detections = result["detections"]
            run_id = get_db().log_run(
                backend=result["backend_used"],
                model_name=selected_model.name if selected_model else "classical_hotspot",
                modality=modality,
                preprocessing_steps=result["preprocessing_steps"],
                detections=detections,
                input_path=source_name,
                output_path=str(output_path),
                metrics={"detection_count": len(detections)},
                notes="Logged from Streamlit inference demo",
            )

            st.session_state["last_inference_result"] = {
                "result": result,
                "output_path": str(output_path),
                "source_name": source_name,
                "run_id": run_id,
                "request_signature": request_signature,
            }
        st.success("Detection finished and the run was saved to SQLite.")

    cached = st.session_state.get("last_inference_result")
    if (
        not cached
        or cached.get("request_signature") != request_signature
        or cached.get("source_name") != source_name
    ):
        right_column.image(
            to_rgb(image), caption=f"Ready for inference: {source_name}", use_container_width=True
        )
        render_panel(
            "Detection outputs",
            "Run the detector to see the annotated frame, confidence table, and export actions.",
        )
        return

    result = cached["result"]
    detections = result["detections"]
    top_confidence = max((detection["confidence"] for detection in detections), default=0.0)
    alert_state = "high" if top_confidence >= 0.75 else "monitor"
    render_metric_cards(
        [
            {
                "label": "Backend used",
                "value": str(result["backend_used"]),
                "foot": "Actual detector chosen for this run",
                "tone": "cool",
            },
            {
                "label": "Detections",
                "value": str(len(detections)),
                "foot": "Bounding boxes produced for the current frame",
                "tone": "warm",
            },
            {
                "label": "Top confidence",
                "value": f"{top_confidence:.2f}",
                "foot": f"Alert state: {alert_state}",
                "tone": "hot",
            },
        ]
    )

    with right_column:
        annotated_col, processed_col = st.columns(2)
        annotated_col.image(
            to_rgb(result["annotated_image"]),
            caption=f"Annotated output ({result['backend_used']})",
            use_container_width=True,
        )
        processed_col.image(
            to_rgb(result["processed_image"]),
            caption="Processed input",
            use_container_width=True,
        )

        st.write("Preprocessing:", ", ".join(result["preprocessing_steps"]) or "None")
        st.write("Saved output:", cached["output_path"])

        actions_col, csv_col = st.columns(2)
        actions_col.download_button(
            "Download annotated image",
            data=image_to_png_bytes(result["annotated_image"]),
            file_name=f"annotated_run_{cached['run_id']}.png",
            mime="image/png",
        )
        detections_df = pd.DataFrame(detections)
        csv_col.download_button(
            "Download detections CSV",
            data=dataframe_to_csv_bytes(detections_df) if not detections_df.empty else b"",
            file_name=f"detections_run_{cached['run_id']}.csv",
            mime="text/csv",
            disabled=detections_df.empty,
        )

        if detections_df.empty:
            st.info("No detections were produced by the selected backend.")
        else:
            st.dataframe(detections_df, use_container_width=True, height=260)


def render_run_history() -> None:
    """Render the SQLite-backed run history page."""
    st.header("Run History")
    database = get_db()
    recent_reports = pd.DataFrame(database.fetch_recent_dataset_reports(limit=10))
    recent_runs = pd.DataFrame(database.fetch_recent_runs(limit=25))

    render_metric_cards(
        [
            {
                "label": "Dataset reports",
                "value": str(len(recent_reports)),
                "foot": "Validation snapshots recorded in SQLite",
                "tone": "cool",
            },
            {
                "label": "Inference runs",
                "value": str(len(recent_runs)),
                "foot": "Logged output sessions available for review",
                "tone": "warm",
            },
            {
                "label": "Latest run",
                "value": str(recent_runs.iloc[0]["backend"]) if not recent_runs.empty else "none",
                "foot": "Most recent detection backend used",
                "tone": "hot",
            },
        ]
    )

    if not recent_runs.empty:
        chart_col, detail_col = st.columns([1.2, 1])
        with chart_col:
            st.subheader("Backend usage")
            backend_counts = (
                recent_runs.groupby("backend").size().reset_index(name="runs")
            )
            st.altair_chart(
                build_bar_chart(
                    backend_counts,
                    x="backend:N",
                    y="runs:Q",
                    color="backend:N",
                    title="Runs",
                ),
                use_container_width=True,
            )
        with detail_col:
            render_panel(
                "Run history summary",
                (
                    f"Most recent source: {html.escape(str(recent_runs.iloc[0]['input_path']))}<br>"
                    f"Most recent output: {html.escape(str(recent_runs.iloc[0]['output_path']))}"
                ),
            )

    st.subheader("Recent dataset reports")
    if recent_reports.empty:
        render_panel(
            "No dataset reports yet",
            "Refresh the manifest from the Dataset Status page to populate validation history.",
        )
    else:
        st.dataframe(recent_reports, use_container_width=True, height=260)
        st.download_button(
            "Download dataset report history CSV",
            data=dataframe_to_csv_bytes(recent_reports),
            file_name="dataset_report_history.csv",
            mime="text/csv",
        )

    st.subheader("Recent inference runs")
    if recent_runs.empty:
        render_panel(
            "No inference runs yet",
            "Use the Inference Demo page to generate annotated outputs and log them here.",
        )
    else:
        st.dataframe(recent_runs, use_container_width=True, height=320)
        st.download_button(
            "Download inference run history CSV",
            data=dataframe_to_csv_bytes(recent_runs),
            file_name="inference_run_history.csv",
            mime="text/csv",
        )


def main() -> None:
    """Run the Streamlit dashboard."""
    inject_custom_css()
    settings = get_settings()
    settings.ensure_runtime_dirs()
    report = load_dataset_report(force_refresh=False)

    with st.sidebar:
        render_sidebar_context(report)
        page = st.radio(
            "Page",
            options=(
                "Overview",
                "Dataset Status",
                "Preprocessing Lab",
                "Inference Demo",
                "Run History",
            ),
        )

    if page == "Overview":
        render_overview(report)
    elif page == "Dataset Status":
        render_dataset_status(report)
    elif page == "Preprocessing Lab":
        render_preprocessing_lab(report)
    elif page == "Inference Demo":
        render_inference_demo(report)
    else:
        render_run_history()


if __name__ == "__main__":
    main()
