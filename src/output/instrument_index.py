"""
EDAI4 - Instrument Index Generator
Generates instrument index deliverable from P&ID graph
"""

from pathlib import Path
from typing import Optional
import pandas as pd

from src.utils import get_logger
from src.topology import PIDGraph, NodeType

logger = get_logger(__name__)


class InstrumentIndexGenerator:
    """
    Generates Instrument Index from P&ID graph.

    The Instrument Index is the master database containing all instruments
    with their tag numbers, descriptions, types, ranges, and P&ID references.
    """

    # Column definitions for instrument index
    COLUMNS = [
        "Tag Number",
        "Service Description",
        "Instrument Type",
        "Measured Variable",
        "Function",
        "Signal Type",
        "Signal Range",
        "P&ID Reference",
        "Location",
        "Manufacturer",
        "Model",
        "Is Safety (SIS)",
        "Remarks",
    ]

    def __init__(self):
        """Initialize instrument index generator."""
        logger.info("InstrumentIndexGenerator initialized")

    def generate(
        self,
        graph: PIDGraph,
        pid_reference: str = "",
    ) -> pd.DataFrame:
        """
        Generate instrument index from P&ID graph.

        Args:
            graph: PIDGraph with instrument nodes
            pid_reference: P&ID drawing reference number

        Returns:
            DataFrame with instrument index data
        """
        data = []

        # Get all instrument nodes
        for node in graph.get_tagged_nodes():
            row = self._create_row(node, pid_reference)
            if row:
                data.append(row)

        # Create DataFrame
        df = pd.DataFrame(data, columns=self.COLUMNS)

        # Sort by tag number
        df = df.sort_values("Tag Number").reset_index(drop=True)

        logger.info(f"Generated instrument index: {len(df)} instruments")
        return df

    def _create_row(self, node, pid_reference: str) -> Optional[dict]:
        """Create a row for an instrument node."""
        if not node.tag:
            return None

        row = {
            "Tag Number": node.tag,
            "Service Description": self._get_description(node),
            "Instrument Type": self._get_instrument_type(node),
            "Measured Variable": self._get_measured_variable(node),
            "Function": self._get_function(node),
            "Signal Type": self._get_signal_type(node),
            "Signal Range": self._get_signal_range(node),
            "P&ID Reference": pid_reference,
            "Location": self._get_location(node),
            "Manufacturer": "",  # To be filled manually
            "Model": "",  # To be filled manually
            "Is Safety (SIS)": self._is_safety(node),
            "Remarks": "",
        }

        return row

    def _get_description(self, node) -> str:
        """Get service description for instrument."""
        if node.tag_info and node.tag_info.description:
            return node.tag_info.description

        return node.label or ""

    def _get_instrument_type(self, node) -> str:
        """Get instrument type."""
        if node.tag_info and node.tag_info.instrument_type:
            return node.tag_info.instrument_type

        return node.detection_class or ""

    def _get_measured_variable(self, node) -> str:
        """Get measured variable (P, T, L, F, etc.)."""
        if node.tag_info and node.tag_info.measured_variable_name:
            return node.tag_info.measured_variable_name

        return ""

    def _get_function(self, node) -> str:
        """Get instrument function."""
        if node.tag_info and node.tag_info.function:
            return node.tag_info.function

        return ""

    def _get_signal_type(self, node) -> str:
        """Get signal type (AI, AO, DI, DO)."""
        if node.signal_info:
            return node.signal_info.signal_code

        return ""

    def _get_signal_range(self, node) -> str:
        """Get signal range."""
        if node.signal_info and node.signal_info.range:
            return node.signal_info.range

        return ""

    def _get_location(self, node) -> str:
        """Get instrument location (Field/Panel)."""
        # Local instruments are in field
        if node.signal_info and node.signal_info.signal_code == "LOCAL":
            return "Field"

        # Instruments with I/O signals connect to control room
        if node.signal_info and node.signal_info.signal_code in ["AI", "AO", "DI", "DO"]:
            return "Field + Control Room"

        return "Field"

    def _is_safety(self, node) -> str:
        """Check if instrument is safety-related."""
        if node.tag_info and node.tag_info.is_safety:
            return "Yes"

        return "No"

    def to_excel(
        self,
        df: pd.DataFrame,
        output_path: str | Path,
        sheet_name: str = "Instrument Index",
    ) -> Path:
        """
        Save instrument index to Excel file.

        Args:
            df: Instrument index DataFrame
            output_path: Output file path
            sheet_name: Excel sheet name

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to Excel with formatting
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            # Set column widths
            column_widths = {
                "A": 15,  # Tag Number
                "B": 35,  # Service Description
                "C": 25,  # Instrument Type
                "D": 18,  # Measured Variable
                "E": 20,  # Function
                "F": 12,  # Signal Type
                "G": 15,  # Signal Range
                "H": 15,  # P&ID Reference
                "I": 15,  # Location
                "J": 15,  # Manufacturer
                "K": 15,  # Model
                "L": 15,  # Is Safety
                "M": 25,  # Remarks
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

            # Freeze header row
            worksheet.freeze_panes = "A2"

        logger.info(f"Saved instrument index to: {output_path}")
        return output_path

    def to_csv(self, df: pd.DataFrame, output_path: str | Path) -> Path:
        """Save instrument index to CSV file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output_path, index=False)
        logger.info(f"Saved instrument index to: {output_path}")

        return output_path
