"""
EDAI4 - Main CLI Entry Point
Extraction of E&I Deliverables from P&ID using Generative AI
"""

import argparse
import sys
from pathlib import Path

from src.utils import setup_logger, get_logger, config, ensure_directory


def main():
    """Main entry point for EDAI4 CLI."""
    parser = argparse.ArgumentParser(
        prog="edai4",
        description="Extract E&I Deliverables from P&ID using Generative AI",
    )

    parser.add_argument(
        "input",
        nargs="?",
        help="Input P&ID file (PDF or image)",
    )

    parser.add_argument(
        "-o", "--output",
        default="./data/output",
        help="Output directory for generated deliverables",
    )

    parser.add_argument(
        "-c", "--config",
        default="./config",
        help="Path to configuration directory",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose/debug logging",
    )

    parser.add_argument(
        "--deliverables",
        nargs="+",
        default=["all"],
        choices=["all", "instrument_index", "io_list", "alarm_list", "cause_effect"],
        help="Deliverables to generate",
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch Streamlit GUI",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="EDAI4 v1.0.0",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logger(level=log_level, log_file="./logs/edai4.log")
    logger = get_logger("main")

    logger.info("EDAI4 - E&I Deliverables Extraction from P&ID")
    logger.info("=" * 50)

    # Load configuration
    try:
        config.load(args.config)
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Launch GUI if requested
    if args.gui:
        logger.info("Launching Streamlit GUI...")
        import subprocess
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "app/main.py", "--server.headless", "true"
        ])
        return

    # Process input file
    if not args.input:
        parser.print_help()
        logger.warning("No input file specified. Use --gui for interactive mode.")
        sys.exit(0)

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Ensure output directory exists
    output_dir = ensure_directory(args.output)
    logger.info(f"Output directory: {output_dir}")

    # Process the P&ID file
    logger.info(f"Processing: {input_path}")

    try:
        # Import processing modules
        from src.ingestion import PDFProcessor, ImagePreprocessor
        from src.perception import SymbolDetector, OCREngine
        from src.topology import GraphBuilder
        from src.deterministic import TagParser, SignalClassifier
        from src.output import (
            InstrumentIndexGenerator,
            IOListGenerator,
            AlarmListGenerator,
            CauseEffectMatrixGenerator,
        )

        # Step 1: Ingest and preprocess
        logger.info("Step 1: Ingesting P&ID file...")
        pdf_processor = PDFProcessor()
        image_preprocessor = ImagePreprocessor()

        if input_path.suffix.lower() == ".pdf":
            images = pdf_processor.extract_pages(input_path)
        else:
            images = [image_preprocessor.load_image(input_path)]

        processed_images = [image_preprocessor.preprocess(img) for img in images]
        logger.info(f"Processed {len(processed_images)} page(s)")

        # Step 2: Detect symbols and extract text
        logger.info("Step 2: Detecting symbols and extracting text...")
        symbol_detector = SymbolDetector()
        ocr_engine = OCREngine()

        all_symbols = []
        all_texts = []

        for img in processed_images:
            symbols = symbol_detector.detect(img)
            texts = ocr_engine.extract_all_text(img)
            all_symbols.extend(symbols)
            all_texts.extend(texts)

        logger.info(f"Detected {len(all_symbols)} symbols, {len(all_texts)} text blocks")

        # Step 3: Build graph
        logger.info("Step 3: Building P&ID graph...")
        graph_builder = GraphBuilder()
        pid_graph = graph_builder.build(all_symbols, all_texts)

        # Step 4: Parse tags and classify signals
        logger.info("Step 4: Parsing instrument tags...")
        tag_parser = TagParser()
        signal_classifier = SignalClassifier()

        for node in pid_graph.nodes:
            if node.tag:
                tag_info = tag_parser.parse(node.tag)
                node.tag_info = tag_info
                node.signal_type = signal_classifier.classify(tag_info)

        # Step 5: Generate deliverables
        logger.info("Step 5: Generating deliverables...")

        deliverables = args.deliverables
        if "all" in deliverables:
            deliverables = ["instrument_index", "io_list", "alarm_list", "cause_effect"]

        if "instrument_index" in deliverables:
            gen = InstrumentIndexGenerator()
            df = gen.generate(pid_graph)
            output_path = output_dir / f"{input_path.stem}_instrument_index.xlsx"
            gen.to_excel(df, output_path)
            logger.info(f"Generated: {output_path}")

        if "io_list" in deliverables:
            gen = IOListGenerator()
            df = gen.generate(pid_graph)
            output_path = output_dir / f"{input_path.stem}_io_list.xlsx"
            gen.to_excel(df, output_path)
            logger.info(f"Generated: {output_path}")

        if "alarm_list" in deliverables:
            gen = AlarmListGenerator()
            df = gen.generate(pid_graph)
            output_path = output_dir / f"{input_path.stem}_alarm_list.xlsx"
            gen.to_excel(df, output_path)
            logger.info(f"Generated: {output_path}")

        if "cause_effect" in deliverables:
            gen = CauseEffectMatrixGenerator()
            df = gen.generate(pid_graph)
            output_path = output_dir / f"{input_path.stem}_cause_effect.xlsx"
            gen.to_excel(df, output_path)
            logger.info(f"Generated: {output_path}")

        logger.info("Processing complete!")
        logger.info(f"Deliverables saved to: {output_dir}")

    except ImportError as e:
        logger.error(f"Module not yet implemented: {e}")
        logger.info("Run 'python -m streamlit run app/main.py' for GUI mode")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise


if __name__ == "__main__":
    main()
