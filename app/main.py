"""
EDAI4 - Streamlit Main Application
Web interface for P&ID E&I deliverables extraction
"""

import streamlit as st
from pathlib import Path
import tempfile
import os

# Page configuration
st.set_page_config(
    page_title="EDAI4 - P&ID E&I Extractor",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    """Initialize session state variables."""
    if "processed" not in st.session_state:
        st.session_state.processed = False
    if "graph" not in st.session_state:
        st.session_state.graph = None
    if "images" not in st.session_state:
        st.session_state.images = []
    if "detections" not in st.session_state:
        st.session_state.detections = []
    if "text_blocks" not in st.session_state:
        st.session_state.text_blocks = []


def main():
    """Main application entry point."""
    init_session_state()

    # Header
    st.title("🔧 EDAI4 - P&ID E&I Deliverables Extractor")
    st.markdown(
        "Extract **Instrument Index**, **I/O List**, **Alarm List**, and "
        "**Cause & Effect Matrix** from P&ID drawings using AI."
    )

    st.divider()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # PDF Processing
        st.subheader("PDF Settings")
        dpi = st.slider("DPI", 150, 600, 300, 50)
        grayscale = st.checkbox("Convert to grayscale", value=True)

        # Detection Settings
        st.subheader("Detection Settings")
        confidence = st.slider("Confidence Threshold", 0.1, 0.9, 0.5, 0.1)

        # Output Settings
        st.subheader("Output Settings")
        pid_reference = st.text_input("P&ID Reference", "P&ID-001")
        plc_name = st.text_input("PLC/DCS Name", "PLC-001")

        st.divider()
        st.markdown(
            "**EDAI4** v1.0.0\n\n"
            "Powered by YOLOv8, EasyOCR, and LangChain"
        )

    # Main content
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📤 Upload P&ID")

        uploaded_file = st.file_uploader(
            "Upload P&ID file (PDF or Image)",
            type=["pdf", "png", "jpg", "jpeg", "tiff"],
            help="Upload a P&ID drawing to extract E&I deliverables",
        )

        if uploaded_file:
            st.success(f"Uploaded: {uploaded_file.name}")

            # Process button
            if st.button("🚀 Process P&ID", type="primary", use_container_width=True):
                with st.spinner("Processing P&ID..."):
                    process_pid(
                        uploaded_file,
                        dpi=dpi,
                        grayscale=grayscale,
                        confidence=confidence,
                        pid_reference=pid_reference,
                        plc_name=plc_name,
                    )

    with col2:
        st.header("📊 Results")

        if st.session_state.processed and st.session_state.graph:
            display_results(pid_reference, plc_name)
        else:
            st.info("Upload and process a P&ID to see results.")

    # Image viewer (full width)
    if st.session_state.images:
        st.divider()
        st.header("🖼️ P&ID Preview")
        display_image_viewer()


def process_pid(
    uploaded_file,
    dpi: int,
    grayscale: bool,
    confidence: float,
    pid_reference: str,
    plc_name: str,
):
    """Process the uploaded P&ID file."""
    try:
        # Import modules
        from src.utils import config
        from src.ingestion import PDFProcessor, ImagePreprocessor
        from src.perception import SymbolDetector, OCREngine
        from src.topology import GraphBuilder, SpatialMatcher

        # Load config
        config.load()

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(uploaded_file.name).suffix
        ) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        # Step 1: Load and preprocess image
        st.text("Step 1/4: Loading and preprocessing...")

        pdf_processor = PDFProcessor(dpi=dpi)
        image_preprocessor = ImagePreprocessor(grayscale=grayscale)

        if uploaded_file.name.lower().endswith(".pdf"):
            images = pdf_processor.extract_pages(tmp_path)
        else:
            import cv2
            image = cv2.imread(tmp_path)
            images = [image]

        processed_images = [image_preprocessor.preprocess(img) for img in images]
        st.session_state.images = processed_images

        # Step 2: Detect symbols
        st.text("Step 2/4: Detecting symbols...")
        symbol_detector = SymbolDetector(confidence_threshold=confidence)

        all_detections = []
        for img in processed_images:
            result = symbol_detector.detect(img)
            all_detections.extend(result.detections)

        st.session_state.detections = all_detections

        # Step 3: Extract text
        st.text("Step 3/4: Extracting text with OCR...")
        ocr_engine = OCREngine()

        all_texts = []
        for img in processed_images:
            result = ocr_engine.extract_all_text(img)
            all_texts.extend(result.text_blocks)

        st.session_state.text_blocks = all_texts

        # Step 4: Build graph
        st.text("Step 4/4: Building knowledge graph...")
        spatial_matcher = SpatialMatcher()
        graph_builder = GraphBuilder()

        # Match text to symbols
        spatial_matcher.match_text_to_symbols(all_texts, all_detections)

        # Build graph
        graph = graph_builder.build(all_detections, all_texts, pid_reference)
        st.session_state.graph = graph

        st.session_state.processed = True

        # Cleanup
        os.unlink(tmp_path)

        st.success("Processing complete!")

    except ImportError as e:
        st.error(f"Missing module: {e}")
        st.info("Please install all requirements: `pip install -r requirements.txt`")
    except Exception as e:
        st.error(f"Processing failed: {e}")
        import traceback
        st.code(traceback.format_exc())


def display_results(pid_reference: str, plc_name: str):
    """Display processing results and generate deliverables."""
    graph = st.session_state.graph

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Nodes", graph.node_count)
    with col2:
        st.metric("Tagged Instruments", len(graph.get_tagged_nodes()))
    with col3:
        st.metric("Symbols Detected", len(st.session_state.detections))
    with col4:
        st.metric("Text Blocks", len(st.session_state.text_blocks))

    st.divider()

    # Deliverable generation
    st.subheader("📋 Generate Deliverables")

    deliverable_options = st.multiselect(
        "Select deliverables to generate",
        ["Instrument Index", "I/O List", "Alarm List", "Cause & Effect Matrix"],
        default=["Instrument Index", "I/O List"],
    )

    if st.button("📥 Generate Selected Deliverables", use_container_width=True):
        generate_deliverables(graph, pid_reference, plc_name, deliverable_options)


def generate_deliverables(graph, pid_reference: str, plc_name: str, options: list):
    """Generate selected deliverables."""
    from src.output import (
        InstrumentIndexGenerator,
        IOListGenerator,
        AlarmListGenerator,
        CauseEffectMatrixGenerator,
    )
    import io

    for option in options:
        st.subheader(f"📄 {option}")

        try:
            if option == "Instrument Index":
                gen = InstrumentIndexGenerator()
                df = gen.generate(graph, pid_reference)
            elif option == "I/O List":
                gen = IOListGenerator()
                df = gen.generate(graph, pid_reference, plc_name)
            elif option == "Alarm List":
                gen = AlarmListGenerator()
                df = gen.generate(graph, pid_reference)
            elif option == "Cause & Effect Matrix":
                gen = CauseEffectMatrixGenerator()
                df = gen.generate(graph, pid_reference)

            # Display preview
            if len(df) > 0:
                st.dataframe(df, use_container_width=True)

                # Download button
                buffer = io.BytesIO()
                df.to_excel(buffer, index=False, engine="openpyxl")
                buffer.seek(0)

                filename = f"{pid_reference}_{option.lower().replace(' ', '_')}.xlsx"
                st.download_button(
                    f"⬇️ Download {option}",
                    data=buffer,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.warning(f"No data found for {option}")

        except Exception as e:
            st.error(f"Failed to generate {option}: {e}")


def display_image_viewer():
    """Display P&ID image with annotations."""
    images = st.session_state.images
    detections = st.session_state.detections
    text_blocks = st.session_state.text_blocks

    if not images:
        return

    # Page selector for multi-page PDFs
    if len(images) > 1:
        page = st.selectbox(
            "Select Page",
            range(len(images)),
            format_func=lambda x: f"Page {x + 1}",
        )
    else:
        page = 0

    # Display options
    col1, col2, col3 = st.columns(3)
    with col1:
        show_symbols = st.checkbox("Show detected symbols", value=True)
    with col2:
        show_text = st.checkbox("Show detected text", value=True)
    with col3:
        show_tags = st.checkbox("Highlight tags", value=True)

    # Get image
    import cv2
    import numpy as np

    image = images[page].copy()

    # Convert grayscale to BGR if needed
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Draw annotations
    if show_symbols:
        for detection in detections:
            bbox = detection.bbox
            x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            if detection.tag_number:
                cv2.putText(
                    image, detection.tag_number, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1
                )

    if show_text:
        for text_block in text_blocks:
            region = text_block.region
            x1, y1, x2, y2 = int(region.x1), int(region.y1), int(region.x2), int(region.y2)

            color = (0, 0, 255) if (show_tags and text_block.is_tag) else (255, 0, 0)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 1)

    # Convert BGR to RGB for display
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    st.image(image_rgb, use_container_width=True)


if __name__ == "__main__":
    main()
