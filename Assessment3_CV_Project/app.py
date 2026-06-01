"""Streamlit GUI for RGB / Thermal single-modality detection and late fusion."""

from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="RescueVision", layout="wide")

PROJECT_ROOT = Path(__file__).parent

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv"}
RGB_EXPECTED_SIZE = (1250, 1000)
THERMAL_EXPECTED_SIZE = (640, 512)


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #070b14 0%, #0f172a 100%);
            color: #e5e7eb;
        }
        .main .block-container {
            max-width: 1240px;
            padding-top: 1.2rem;
            padding-bottom: 2.4rem;
        }
        [data-testid="stSidebar"] {
            background: #0b1220;
            border-right: 1px solid rgba(255,255,255,0.08);
        }
        [data-testid="stSidebar"] * { color: #e5e7eb !important; }
        h1, h2, h3, h4, p, li, label, span { color: #e5e7eb !important; }
        .hero {
            border-radius: 18px;
            padding: 1.2rem 1.3rem;
            border: 1px solid rgba(255,255,255,0.12);
            background:
                radial-gradient(circle at 0% 0%, rgba(59,130,246,0.35), transparent 35%),
                radial-gradient(circle at 100% 0%, rgba(236,72,153,0.25), transparent 30%),
                #111827;
            box-shadow: 0 18px 36px rgba(0, 0, 0, 0.32);
        }
        .hero-title { font-size: 1.8rem; margin: 0; font-weight: 700; color: #f8fafc; }
        .hero-sub { margin-top: .4rem; color: #cbd5e1 !important; }
        .card {
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,.12);
            background: rgba(17,24,39,.72);
            padding: .9rem 1rem;
            transition: transform .18s ease, box-shadow .18s ease;
            box-shadow: 0 10px 22px rgba(0,0,0,.25);
            min-height: 122px;
        }
        .card:hover { transform: translateY(-2px); box-shadow: 0 14px 28px rgba(0,0,0,.32); }
        .kpi {
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,.10);
            background: rgba(2,6,23,.55);
            padding: .7rem .9rem;
            margin-bottom: .6rem;
        }
        .kpi-title { color: #94a3b8 !important; font-size: .82rem; }
        .kpi-value { color: #f8fafc !important; font-size: 1.5rem; font-weight: 700; }
        .panel {
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,.12);
            background: rgba(17,24,39,.72);
            padding: 1rem;
        }
        .stSelectbox div[data-baseweb="select"], .stTextInput input, .stNumberInput input {
            background: #0b1220 !important;
            color: #f8fafc !important;
            border: 1px solid rgba(255,255,255,.18) !important;
        }
        .stFileUploader > div {
            background: rgba(2,6,23,.45);
            border: 1px dashed rgba(255,255,255,.22);
            border-radius: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            color: #cbd5e1 !important;
            border: 1px solid rgba(255,255,255,.15);
            border-radius: 999px;
            background: rgba(2,6,23,.45);
            margin-right: .35rem;
            padding: .45rem .9rem;
        }
        .stTabs [aria-selected="true"] {
            color: #f8fafc !important;
            background: rgba(59,130,246,.22);
            border-color: rgba(59,130,246,.6);
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(255,255,255,.12);
            border-radius: 12px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------


@st.cache_resource
def load_yolo_model(model_path: str):
    from ultralytics import YOLO  # type: ignore

    return YOLO(model_path)


@st.cache_resource
def load_fusion_runner(rgb_path: str, thermal_path: str):
    from sar_vision.inference import LateFusionRunner

    return LateFusionRunner(
        rgb_model_path=rgb_path,
        thermal_model_path=thermal_path,
    )


def ensure_state() -> None:
    if "model_paths" not in st.session_state:
        st.session_state["model_paths"] = {
            "RGB": str(PROJECT_ROOT / "artifacts" / "models" / "rgb_best_26s.pt"),
            "Thermal": str(PROJECT_ROOT / "artifacts" / "models" / "Thermal_yolo26m.pt"),
        }
    if "cropped_rgb_dir" not in st.session_state:
        st.session_state["cropped_rgb_dir"] = ""
    if "cropped_rgb_count" not in st.session_state:
        st.session_state["cropped_rgb_count"] = 0


# ---------------------------------------------------------------------------
# Helpers - single-modality
# ---------------------------------------------------------------------------


def uploaded_to_image(uploaded_file) -> np.ndarray:
    image_bytes = np.frombuffer(uploaded_file.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode uploaded image.")
    return image


def result_to_dataframe(result) -> pd.DataFrame:
    rows: List[Dict[str, float]] = []
    names = result.names
    for box in result.boxes:
        class_id = int(box.cls[0].item())
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        rows.append(
            {
                "label": names.get(class_id, str(class_id)),
                "confidence": round(float(box.conf[0].item()), 3),
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            }
        )
    return pd.DataFrame(rows)


def run_image_single(image: np.ndarray, model_path: str, conf: float) -> Tuple[np.ndarray, pd.DataFrame]:
    model = load_yolo_model(model_path)
    result = model.predict(image, conf=conf, verbose=False)[0]
    return result.plot(), result_to_dataframe(result)


def run_video_single(video_file, model_path: str, conf: float, max_frames: int) -> Tuple[bytes, pd.DataFrame]:
    model = load_yolo_model(model_path)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        in_path = temp_path / "input.mp4"
        out_path = temp_path / "output.mp4"
        in_path.write_bytes(video_file.getvalue())

        cap = cv2.VideoCapture(str(in_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

        frame_count = 0
        detection_count = 0
        confidences: List[float] = []
        progress = st.progress(0.0, text="Processing video...")

        while cap.isOpened() and frame_count < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            result = model.predict(frame, conf=conf, verbose=False)[0]
            writer.write(result.plot())
            detection_count += len(result.boxes)
            for box in result.boxes:
                confidences.append(float(box.conf[0].item()))
            frame_count += 1
            progress.progress(min(frame_count / max_frames, 1.0), text=f"Processed {frame_count} frames")

        cap.release()
        writer.release()
        progress.empty()

        summary = pd.DataFrame(
            [
                {
                    "frames_processed": frame_count,
                    "total_detections": detection_count,
                    "avg_confidence": round(float(np.mean(confidences)) if confidences else 0.0, 3),
                }
            ]
        )
        return out_path.read_bytes(), summary


# ---------------------------------------------------------------------------
# Helpers - multimodal late fusion
# ---------------------------------------------------------------------------


def _extract_zip_into(zip_bytes: bytes, target_dir: Path) -> int:
    count = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            name = Path(member.filename).name
            if not name or name.startswith("."):
                continue
            if Path(name).suffix.lower() not in IMAGE_EXTS:
                continue
            target_path = target_dir / name
            with zf.open(member) as src, open(target_path, "wb") as dst:
                dst.write(src.read())
            count += 1
    return count


def _save_uploaded_files(uploaded_files, target_dir: Path) -> int:
    count = 0
    for up in uploaded_files or []:
        if Path(up.name).suffix.lower() not in IMAGE_EXTS:
            continue
        (target_dir / Path(up.name).name).write_bytes(up.getvalue())
        count += 1
    return count


def materialise_images(zip_file, image_files, target_dir: Path, label: str) -> int:
    """Drop uploaded images (ZIP and/or multi-file) into ``target_dir``.

    Returns the total number of image files written.
    """

    written = 0
    if zip_file is not None:
        try:
            written += _extract_zip_into(zip_file.getvalue(), target_dir)
        except zipfile.BadZipFile:
            st.error(f"{label}: ZIP file appears to be corrupted.")
    written += _save_uploaded_files(image_files, target_dir)
    return written


def _extract_zip_labels(zip_bytes: bytes, target_dir: Path) -> int:
    count = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            name = Path(member.filename).name
            if not name or name.startswith(".") or Path(name).suffix.lower() != ".txt":
                continue
            target_path = target_dir / name
            with zf.open(member) as src, open(target_path, "wb") as dst:
                dst.write(src.read())
            count += 1
    return count


def _save_uploaded_labels(uploaded_files, target_dir: Path) -> int:
    count = 0
    for up in uploaded_files or []:
        if Path(up.name).suffix.lower() != ".txt":
            continue
        (target_dir / Path(up.name).name).write_bytes(up.getvalue())
        count += 1
    return count


def materialise_labels(zip_file, label_files, target_dir: Path) -> int:
    written = 0
    if zip_file is not None:
        try:
            written += _extract_zip_labels(zip_file.getvalue(), target_dir)
        except zipfile.BadZipFile:
            st.error("Label ZIP file appears to be corrupted.")
    written += _save_uploaded_labels(label_files, target_dir)
    return written


def zip_directory(source_dir: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=path.relative_to(source_dir))
    return buffer.getvalue()


def list_rgb_images_for_fusion(image_dir: Path) -> List[Path]:
    from sar_vision.preprocessing import list_rgb_images

    return list_rgb_images(image_dir)


def gallery(image_paths: List[Path], cols: int = 3, limit: int = 12) -> None:
    if not image_paths:
        st.info("No images to display.")
        return
    shown = image_paths[:limit]
    rows = (len(shown) + cols - 1) // cols
    for r in range(rows):
        chunk = shown[r * cols : (r + 1) * cols]
        cols_ui = st.columns(len(chunk))
        for col, path in zip(cols_ui, chunk):
            img = cv2.imread(str(path))
            if img is None:
                continue
            col.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption=path.name, use_container_width=True)
    if len(image_paths) > limit:
        st.caption(f"Showing first {limit} of {len(image_paths)} images.")


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


def home_page() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">RescueVision Detection Console</div>
            <div class="hero-sub">
                Run RGB only, Thermal only, or fuse both with late fusion to detect
                people in search-and-rescue imagery.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="card"><b>RGB only</b><br>Visible-spectrum drone footage. Single image or video.</div>', unsafe_allow_html=True)
    c2.markdown('<div class="card"><b>Thermal only</b><br>Heat signatures for night/low visibility. Single image or video.</div>', unsafe_allow_html=True)
    c3.markdown('<div class="card"><b>Multimodal (Late Fusion)</b><br>Run RGB + Thermal in parallel and fuse predictions by IoU.</div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("### Workflow")
    st.markdown(
        "1. Open **Model Setup** and verify the RGB and Thermal model paths.\n"
        "2. For multimodal fusion, open **Data Pre-processing** to crop raw RGB images to 1250 x 1000.\n"
        "3. Open **Inference** and pick an approach.\n"
        "4. Upload inputs (cropped RGB + thermal for late fusion), run detection, and download results."
    )


def model_setup_page() -> None:
    st.markdown("## Model Setup")
    st.caption(
        "Set file paths for the RGB and Thermal YOLO checkpoints. "
        "Multimodal uses these two models together via late fusion - no separate model file is needed."
    )
    model_paths = st.session_state["model_paths"]
    found_count = 0
    for key in ["RGB", "Thermal"]:
        model_paths[key] = st.text_input(f"{key} model path", value=model_paths[key])
        if Path(model_paths[key]).exists():
            st.success(f"{key}: found")
            found_count += 1
        else:
            st.warning(f"{key}: file not found")

    st.progress(found_count / 2.0)
    st.caption(f"Model readiness: {found_count}/2")


def preprocessing_page() -> None:
    st.markdown("## Data Pre-processing")
    st.caption(
        "Crop raw RGB images to 1250 x 1000 before multimodal late fusion. "
        "The multimodal pipeline expects cropped/aligned RGB frames, not raw full-frame RGB."
    )

    st.markdown(
        '<div class="panel">'
        "<b>Input requirements</b><br>"
        "• Raw, uncropped RGB frames (.jpg, .jpeg, .png)<br>"
        "• Optional YOLO labels: <code>class_id x_center y_center width height</code> "
        "(normalised to the original image)<br>"
        "• Crop settings: 1250 x 1000 with centre shift (12, 18)"
        "</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    left, right = st.columns([1, 1.8])
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("**Raw RGB images**")
        rgb_zip = st.file_uploader("RGB ZIP", type=["zip"], key="pre_rgb_zip")
        rgb_files = st.file_uploader(
            "or RGB image files",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="pre_rgb_files",
        )
        st.markdown("**Optional YOLO labels**")
        label_zip = st.file_uploader("Label ZIP", type=["zip"], key="pre_label_zip")
        label_files = st.file_uploader(
            "or label .txt files",
            type=["txt"],
            accept_multiple_files=True,
            key="pre_label_files",
        )
        run_clicked = st.button(
            "Preprocess RGB Images", type="primary", use_container_width=True, key="pre_run"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        if not run_clicked:
            if st.session_state.get("cropped_rgb_dir") and Path(st.session_state["cropped_rgb_dir"]).exists():
                prev_dir = Path(st.session_state["cropped_rgb_dir"])
                prev_count = st.session_state.get("cropped_rgb_count", 0)
                st.info(
                    f"Last preprocessing run: **{prev_count}** cropped images saved at "
                    f"`{prev_dir}`. These are available on the Inference page for late fusion."
                )
                gallery(sorted(prev_dir.glob("*.jpg")) + sorted(prev_dir.glob("*.png")))
            else:
                st.write("Upload raw RGB images and click **Preprocess RGB Images**.")
            return

        if rgb_zip is None and not rgb_files:
            st.error("Please upload a ZIP or one or more raw RGB images.")
            return

        work_root = Path(tempfile.mkdtemp(prefix="rescue_preprocess_"))
        raw_dir = work_root / "raw"
        label_dir = work_root / "labels"
        out_img_dir = work_root / "cropped" / "images"
        out_label_dir = work_root / "cropped" / "labels"
        raw_dir.mkdir()
        label_dir.mkdir()

        rgb_n = materialise_images(rgb_zip, rgb_files, raw_dir, "RGB")
        label_n = materialise_labels(label_zip, label_files, label_dir)

        if rgb_n == 0:
            st.error("No valid RGB images found in the upload.")
            return

        try:
            from sar_vision.preprocessing import RgbCropPreprocessor

            preprocessor = RgbCropPreprocessor()
            progress = st.progress(0.0, text="Cropping RGB images...")

            def cb(done, total, name):
                progress.progress(min(done / max(total, 1), 1.0), text=f"Cropping {name} ({done}/{total})")

            with st.spinner("Running RGB crop preprocessing..."):
                report = preprocessor.process_folder(
                    image_input_dir=raw_dir,
                    image_output_dir=out_img_dir,
                    label_input_dir=label_dir if label_n > 0 else None,
                    label_output_dir=out_label_dir if label_n > 0 else None,
                    progress_cb=cb,
                )
            progress.empty()
        except Exception as exc:
            st.error(f"Preprocessing failed: {exc}")
            return

        st.session_state["cropped_rgb_dir"] = str(out_img_dir)
        st.session_state["cropped_rgb_count"] = report.success_count

        st.success("RGB preprocessing complete.")
        k1, k2, k3 = st.columns(3)
        k1.markdown(
            f'<div class="kpi"><div class="kpi-title">Input images</div><div class="kpi-value">{report.input_count}</div></div>',
            unsafe_allow_html=True,
        )
        k2.markdown(
            f'<div class="kpi"><div class="kpi-title">Cropped</div><div class="kpi-value">{report.success_count}</div></div>',
            unsafe_allow_html=True,
        )
        k3.markdown(
            f'<div class="kpi"><div class="kpi-title">Skipped</div><div class="kpi-value">{report.skipped_count}</div></div>',
            unsafe_allow_html=True,
        )

        st.markdown(f"**Output folder:** `{out_img_dir}`")
        if report.skipped_count:
            with st.expander("Skipped files"):
                for msg in report.messages:
                    st.write(msg)

        gallery(report.cropped_paths)
        st.download_button(
            "Download cropped RGB (ZIP)",
            data=zip_directory(out_img_dir),
            file_name="cropped_rgb.zip",
            mime="application/zip",
            use_container_width=True,
        )


def _render_single_modality(approach: str) -> None:
    model_path = st.session_state["model_paths"][approach]
    left, right = st.columns([1, 1.8])
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.caption("Upload either an image (jpg / png / bmp) or a video (mp4 / avi / mov). The app auto-detects the type.")
        conf_threshold = st.slider("Confidence threshold", 0.10, 0.90, 0.25, 0.05, key=f"single_conf_{approach}")
        max_frames = st.number_input(
            "Max video frames", min_value=10, max_value=5000, value=300, step=10, key=f"single_maxf_{approach}"
        )
        uploaded = st.file_uploader(
            "Upload file",
            type=["jpg", "jpeg", "png", "bmp", "mp4", "avi", "mov", "mkv"],
            key=f"single_upload_{approach}",
        )
        run_clicked = st.button("Run Detection", type="primary", use_container_width=True, key=f"single_run_{approach}")
        st.markdown("</div>", unsafe_allow_html=True)

    suffix = Path(uploaded.name).suffix.lower() if uploaded is not None else ""
    if suffix in VIDEO_EXTS:
        input_type = "Video"
    elif suffix in IMAGE_EXTS:
        input_type = "Image"
    else:
        input_type = "Image"

    with right:
        st.info(f"Approach: {approach} only | Detected: {input_type if uploaded else 'no file'}")
        if uploaded is None:
            st.write("Upload a file to begin.")
            return
        if suffix not in IMAGE_EXTS and suffix not in VIDEO_EXTS:
            st.error(f"Unsupported file type: {suffix or 'unknown'}")
            return
        if not Path(model_path).exists():
            st.error(f"Model file not found: {model_path}")
            return
        if not run_clicked:
            st.write("Click **Run Detection** to start.")
            return

        try:
            if input_type == "Image":
                with st.spinner("Running image inference..."):
                    image = uploaded_to_image(uploaded)
                    annotated_image, detections_df = run_image_single(image, model_path, conf_threshold)

                preview_tab, table_tab = st.tabs(["Preview", "Detections"])
                with preview_tab:
                    ocol, acol = st.columns(2)
                    ocol.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), caption="Original", use_container_width=True)
                    acol.image(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB), caption="Annotated", use_container_width=True)

                with table_tab:
                    if detections_df.empty:
                        st.warning("No detections found.")
                    else:
                        k1, k2, k3 = st.columns(3)
                        k1.markdown(
                            '<div class="kpi"><div class="kpi-title">Detections</div><div class="kpi-value">{}</div></div>'.format(len(detections_df)),
                            unsafe_allow_html=True,
                        )
                        k2.markdown(
                            '<div class="kpi"><div class="kpi-title">Top confidence</div><div class="kpi-value">{:.2f}</div></div>'.format(float(detections_df["confidence"].max())),
                            unsafe_allow_html=True,
                        )
                        k3.markdown(
                            '<div class="kpi"><div class="kpi-title">Average confidence</div><div class="kpi-value">{:.2f}</div></div>'.format(float(detections_df["confidence"].mean())),
                            unsafe_allow_html=True,
                        )
                        st.dataframe(detections_df, use_container_width=True, height=300)

                success, encoded = cv2.imencode(".png", annotated_image)
                if success:
                    dcol1, dcol2 = st.columns(2)
                    dcol1.download_button(
                        "Download annotated image",
                        data=encoded.tobytes(),
                        file_name="annotated_output.png",
                        mime="image/png",
                        use_container_width=True,
                    )
                    if not detections_df.empty:
                        dcol2.download_button(
                            "Download detections CSV",
                            data=detections_df.to_csv(index=False).encode("utf-8"),
                            file_name="detections.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )
            else:
                with st.spinner("Running video inference..."):
                    video_bytes, summary_df = run_video_single(uploaded, model_path, conf_threshold, int(max_frames))
                st.video(video_bytes)
                k1, k2, k3 = st.columns(3)
                k1.markdown(
                    '<div class="kpi"><div class="kpi-title">Frames processed</div><div class="kpi-value">{}</div></div>'.format(int(summary_df.iloc[0]["frames_processed"])),
                    unsafe_allow_html=True,
                )
                k2.markdown(
                    '<div class="kpi"><div class="kpi-title">Total detections</div><div class="kpi-value">{}</div></div>'.format(int(summary_df.iloc[0]["total_detections"])),
                    unsafe_allow_html=True,
                )
                k3.markdown(
                    '<div class="kpi"><div class="kpi-title">Average confidence</div><div class="kpi-value">{:.2f}</div></div>'.format(float(summary_df.iloc[0]["avg_confidence"])),
                    unsafe_allow_html=True,
                )
                st.dataframe(summary_df, use_container_width=True)
                st.download_button(
                    "Download annotated video",
                    data=video_bytes,
                    file_name="annotated_video.mp4",
                    mime="video/mp4",
                    use_container_width=True,
                )
        except Exception as exc:
            st.error(f"Inference failed: {exc}")


def _render_late_fusion() -> None:
    rgb_path = st.session_state["model_paths"]["RGB"]
    thermal_path = st.session_state["model_paths"]["Thermal"]

    if not Path(rgb_path).exists() or not Path(thermal_path).exists():
        st.error("Both RGB and Thermal model files must exist (see Model Setup).")
        return

    st.markdown(
        '<div class="panel">Multimodal late fusion runs the RGB and Thermal YOLO models '
        "separately, maps RGB detections into the thermal coordinate space, and merges them "
        "by IoU.<br><br>"
        "<b>RGB input must be cropped 1250 x 1000.</b> Prepare raw RGB on the "
        "<b>Data Pre-processing</b> page first, or upload already-cropped RGB frames below."
        "</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    input_kind = st.radio("Input type", ["Images", "Videos"], horizontal=True, key="fusion_input_kind")

    with st.expander("Advanced options", expanded=False):
        col_a, col_b, col_c = st.columns(3)
        rgb_conf = col_a.slider("RGB confidence", 0.05, 0.90, 0.25, 0.05, key="fusion_rgb_conf")
        thermal_conf = col_b.slider("Thermal confidence", 0.05, 0.90, 0.25, 0.05, key="fusion_thermal_conf")
        iou_threshold = col_c.slider("Fusion IoU", 0.10, 0.90, 0.35, 0.05, key="fusion_iou")
        max_frames = st.number_input(
            "Max video frames per side", min_value=10, max_value=5000, value=200, step=10, key="fusion_maxf"
        )

    if input_kind == "Images":
        cropped_dir = st.session_state.get("cropped_rgb_dir", "")
        has_preprocessed = bool(cropped_dir) and Path(cropped_dir).exists()
        pre_count = st.session_state.get("cropped_rgb_count", 0)

        use_preprocessed = False
        if has_preprocessed:
            use_preprocessed = st.checkbox(
                f"Use preprocessed RGB from Data Pre-processing ({pre_count} cropped images)",
                value=True,
                key="fusion_use_preprocessed",
            )

        left, right = st.columns(2)
        with left:
            st.markdown("**RGB cropped frames (1250 x 1000)**")
            if use_preprocessed:
                st.info(f"Using `{cropped_dir}`")
                rgb_zip = None
                rgb_files = None
            else:
                rgb_zip = st.file_uploader("RGB ZIP", type=["zip"], key="rgb_zip")
                rgb_files = st.file_uploader(
                    "or cropped RGB image files",
                    type=["jpg", "jpeg", "png", "bmp"],
                    accept_multiple_files=True,
                    key="rgb_files",
                )
        with right:
            st.markdown("**Thermal frames (640 x 512 expected)**")
            thermal_zip = st.file_uploader("Thermal ZIP", type=["zip"], key="thermal_zip")
            thermal_files = st.file_uploader(
                "or Thermal image files",
                type=["jpg", "jpeg", "png", "bmp"],
                accept_multiple_files=True,
                key="thermal_files",
            )
        run_clicked = st.button("Run Late Fusion", type="primary", use_container_width=True, key="fusion_run_imgs")
        if not run_clicked:
            st.caption(
                "Filenames must end with a numeric frame id after the final underscore, "
                "e.g. `abc_rgb_000001.jpg` and `xyz_thermal_001.jpg` both match frame 1."
            )
            return

        _execute_fusion_images(
            rgb_zip=rgb_zip,
            rgb_files=rgb_files,
            thermal_zip=thermal_zip,
            thermal_files=thermal_files,
            rgb_model_path=rgb_path,
            thermal_model_path=thermal_path,
            rgb_conf=rgb_conf,
            thermal_conf=thermal_conf,
            iou_threshold=iou_threshold,
            rgb_dir_override=Path(cropped_dir) if use_preprocessed else None,
        )
    else:
        left, right = st.columns(2)
        with left:
            rgb_video = st.file_uploader(
                "RGB video", type=["mp4", "avi", "mov"], key="rgb_video"
            )
        with right:
            thermal_video = st.file_uploader(
                "Thermal video", type=["mp4", "avi", "mov"], key="thermal_video"
            )
        run_clicked = st.button("Run Late Fusion", type="primary", use_container_width=True, key="fusion_run_vids")
        if not run_clicked:
            st.caption("Frames are paired by index. Both videos should have the same frame rate and content alignment.")
            return

        if rgb_video is None or thermal_video is None:
            st.error("Please upload both an RGB video and a Thermal video.")
            return

        _execute_fusion_videos(
            rgb_video=rgb_video,
            thermal_video=thermal_video,
            rgb_model_path=rgb_path,
            thermal_model_path=thermal_path,
            rgb_conf=rgb_conf,
            thermal_conf=thermal_conf,
            iou_threshold=iou_threshold,
            max_frames=int(max_frames),
        )


def _make_runner(
    rgb_model_path: str,
    thermal_model_path: str,
    rgb_conf: float,
    thermal_conf: float,
    iou_threshold: float,
):
    runner = load_fusion_runner(rgb_model_path, thermal_model_path)
    runner.rgb_conf = rgb_conf
    runner.thermal_conf = thermal_conf
    runner.iou_threshold = iou_threshold
    return runner


def _show_fusion_results(report, output_dir: Path) -> None:
    st.success(
        f"Matched {report.matched_pairs} pairs "
        f"(RGB {report.rgb_count}, Thermal {report.thermal_count})."
    )
    if report.missing_thermal:
        st.warning(f"{len(report.missing_thermal)} RGB frames had no thermal match.")
    if report.missing_rgb:
        st.warning(f"{len(report.missing_rgb)} thermal frames had no RGB match.")
    if report.skipped_files:
        st.info(f"Skipped {len(report.skipped_files)} files without a numeric frame id.")

    df = pd.DataFrame(report.per_frame)
    if df.empty:
        st.warning("No matched frames produced fused detections.")
        return

    total_dets = int(df["fused_detections"].sum())
    avg_conf = float(df.loc[df["fused_detections"] > 0, "avg_conf"].mean() or 0.0)
    frames_hit = int((df["fused_detections"] > 0).sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(
        f'<div class="kpi"><div class="kpi-title">Matched pairs</div><div class="kpi-value">{report.matched_pairs}</div></div>',
        unsafe_allow_html=True,
    )
    k2.markdown(
        f'<div class="kpi"><div class="kpi-title">Fused detections</div><div class="kpi-value">{total_dets}</div></div>',
        unsafe_allow_html=True,
    )
    k3.markdown(
        f'<div class="kpi"><div class="kpi-title">Frames with hits</div><div class="kpi-value">{frames_hit}</div></div>',
        unsafe_allow_html=True,
    )
    k4.markdown(
        f'<div class="kpi"><div class="kpi-title">Avg confidence</div><div class="kpi-value">{avg_conf:.2f}</div></div>',
        unsafe_allow_html=True,
    )

    thermal_tab, rgb_tab, labels_tab, summary_tab = st.tabs(
        ["Thermal view", "RGB view", "Labels", "Summary"]
    )
    thermal_imgs = sorted(output_dir.glob("fused_thermal_frame_*.jpg"))
    rgb_imgs = sorted(output_dir.glob("fused_rgb_frame_*.jpg"))
    label_files = sorted(output_dir.glob("fused_frame_*.txt"))

    with thermal_tab:
        gallery(thermal_imgs)
    with rgb_tab:
        gallery(rgb_imgs)
    with labels_tab:
        if not label_files:
            st.info("No label files were produced.")
        else:
            for path in label_files[:5]:
                st.markdown(f"**{path.name}**")
                st.code(path.read_text() or "(no detections)", language="text")
            if len(label_files) > 5:
                st.caption(f"Showing 5 of {len(label_files)} label files.")
    with summary_tab:
        st.dataframe(df, use_container_width=True, height=320)

    st.download_button(
        "Download fusion output (ZIP)",
        data=zip_directory(output_dir),
        file_name="late_fusion_output.zip",
        mime="application/zip",
        use_container_width=True,
    )


def _execute_fusion_images(
    rgb_zip,
    rgb_files,
    thermal_zip,
    thermal_files,
    rgb_model_path: str,
    thermal_model_path: str,
    rgb_conf: float,
    thermal_conf: float,
    iou_threshold: float,
    rgb_dir_override: Optional[Path] = None,
) -> None:
    work_root = Path(tempfile.mkdtemp(prefix="rescue_fusion_"))
    thermal_dir = work_root / "thermal"
    output_dir = work_root / "output"
    thermal_dir.mkdir()
    output_dir.mkdir()

    if rgb_dir_override is not None:
        rgb_dir = rgb_dir_override
        rgb_n = len(list_rgb_images_for_fusion(rgb_dir))
    else:
        rgb_dir = work_root / "rgb"
        rgb_dir.mkdir()
        rgb_n = materialise_images(rgb_zip, rgb_files, rgb_dir, "RGB")

    thermal_n = materialise_images(thermal_zip, thermal_files, thermal_dir, "Thermal")

    if rgb_n == 0 or thermal_n == 0:
        st.error("Please provide cropped RGB images (from Data Pre-processing or upload) and thermal images.")
        return

    st.write(f"Loaded {rgb_n} RGB cropped and {thermal_n} thermal frames.")

    try:
        runner = _make_runner(rgb_model_path, thermal_model_path, rgb_conf, thermal_conf, iou_threshold)
        progress = st.progress(0.0, text="Fusing frames...")

        def cb(done, total, fid):
            progress.progress(min(done / max(total, 1), 1.0), text=f"Frame {fid} ({done}/{total})")

        with st.spinner("Running late fusion..."):
            report = runner.run_folder_pair(rgb_dir, thermal_dir, output_dir, progress_cb=cb)
        progress.empty()
    except Exception as exc:
        st.error(f"Late fusion failed: {exc}")
        return

    _show_fusion_results(report, output_dir)


def _execute_fusion_videos(
    rgb_video,
    thermal_video,
    rgb_model_path: str,
    thermal_model_path: str,
    rgb_conf: float,
    thermal_conf: float,
    iou_threshold: float,
    max_frames: int,
) -> None:
    work_root = Path(tempfile.mkdtemp(prefix="rescue_fusion_vid_"))
    rgb_path = work_root / f"rgb{Path(rgb_video.name).suffix or '.mp4'}"
    thermal_path = work_root / f"thermal{Path(thermal_video.name).suffix or '.mp4'}"
    output_dir = work_root / "output"
    output_dir.mkdir()
    rgb_path.write_bytes(rgb_video.getvalue())
    thermal_path.write_bytes(thermal_video.getvalue())

    try:
        runner = _make_runner(rgb_model_path, thermal_model_path, rgb_conf, thermal_conf, iou_threshold)
        progress = st.progress(0.0, text="Fusing video frames...")

        def cb(done, total, fid):
            progress.progress(min(done / max(total, 1), 1.0), text=f"Frame {fid} ({done}/{total})")

        with st.spinner("Running late fusion on videos..."):
            report = runner.run_video_pair(
                rgb_path, thermal_path, output_dir, max_frames=max_frames, progress_cb=cb
            )
        progress.empty()
    except Exception as exc:
        st.error(f"Late fusion failed: {exc}")
        return

    _show_fusion_results(report, output_dir)


def inference_page() -> None:
    st.markdown("## Inference")
    approach = st.selectbox(
        "Approach",
        ["RGB only", "Thermal only", "Multimodal (Late Fusion)"],
        key="approach_select",
    )

    if approach == "RGB only":
        _render_single_modality("RGB")
    elif approach == "Thermal only":
        _render_single_modality("Thermal")
    else:
        _render_late_fusion()


def about_page() -> None:
    st.markdown("## About")
    st.markdown(
        "- Built for Assignment 3 SAR use case.\n"
        "- Supports RGB only, Thermal only, and Multimodal (late fusion) approaches.\n"
        "- **Data Pre-processing** crops raw RGB to 1250 x 1000 for multimodal fusion.\n"
        "- Late fusion runs both YOLO models, maps RGB boxes into the thermal coordinate "
        "space, and merges by IoU. See `sar_vision/inference/fusion.py`."
    )


def main() -> None:
    ensure_state()
    inject_styles()

    with st.sidebar:
        st.title("RescueVision")
        page = st.radio(
            "Navigation",
            ["Home", "Model Setup", "Data Pre-processing", "Inference", "About"],
        )
        st.caption("YOLO Person Detection")

    if page == "Home":
        home_page()
    elif page == "Model Setup":
        model_setup_page()
    elif page == "Data Pre-processing":
        preprocessing_page()
    elif page == "Inference":
        inference_page()
    else:
        about_page()


if __name__ == "__main__":
    main()
