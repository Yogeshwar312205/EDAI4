"""
EDAI4 - I/O List Generator
Generates I/O List deliverable from P&ID graph
"""

from pathlib import Path
from typing import Optional
import pandas as pd

from src.utils import get_logger
from src.topology import PIDGraph, NodeType
from src.deterministic import SignalType

logger = get_logger(__name__)


class IOListGenerator:
    """
    Generates I/O List from P&ID graph.

    The I/O List maps field instruments to PLC/DCS modules,
    specifying signal types, channels, and wiring information.
    """

    # Column definitions for I/O list
    COLUMNS = [
        "Tag Number",
        "Service Description",
        "I/O Type",
        "Signal Type",
        "Signal Range",
        "PLC/DCS",
        "Rack",
        "Slot",
        "Channel",
        "Module Type",
        "Terminal",
        "Cable Number",
        "Junction Box",
        "P&ID Reference",
        "Remarks",
    ]

    def __init__(self):
        """Initialize I/O list generator."""
        self._ai_counter = 0
        self._ao_counter = 0
        self._di_counter = 0
        self._do_counter = 0

        logger.info("IOListGenerator initialized")

    def generate(
        self,
        graph: PIDGraph,
        pid_reference: str = "",
        plc_name: str = "PLC-001",
    ) -> pd.DataFrame:
        """
        Generate I/O list from P&ID graph.

        Args:
            graph: PIDGraph with instrument nodes
            pid_reference: P&ID drawing reference number
            plc_name: PLC/DCS system name

        Returns:
            DataFrame with I/O list data
        """
        data = []

        # Reset counters
        self._ai_counter = 0
        self._ao_counter = 0
        self._di_counter = 0
        self._do_counter = 0

        # Get all nodes with I/O signals
        for node in graph.get_tagged_nodes():
            if not node.signal_info:
                continue

            # Skip local-only instruments
            if node.signal_info.signal_code == "LOCAL":
                continue

            rows = self._create_rows(node, pid_reference, plc_name)
            data.extend(rows)

        # Create DataFrame
        df = pd.DataFrame(data, columns=self.COLUMNS)

        # Sort by I/O type then tag number
        df = df.sort_values(["I/O Type", "Tag Number"]).reset_index(drop=True)

        logger.info(f"Generated I/O list: {len(df)} I/O points")
        return df

    def _create_rows(self, node, pid_reference: str, plc_name: str) -> list[dict]:
        """Create rows for an instrument node (may have multiple I/O)."""
        rows = []

        signal_code = node.signal_info.signal_code

        # Handle combined signals (e.g., "AI+AO" for controllers)
        if "+" in signal_code:
            signal_types = signal_code.split("+")
        else:
            signal_types = [signal_code]

        for sig_type in signal_types:
            row = self._create_single_row(node, sig_type, pid_reference, plc_name)
            if row:
                rows.append(row)

        return rows

    def _create_single_row(
        self,
        node,
        signal_type: str,
        pid_reference: str,
        plc_name: str
    ) -> Optional[dict]:
        """Create a single I/O row."""
        if signal_type not in ["AI", "AO", "DI", "DO"]:
            return None

        # Get channel assignment
        rack, slot, channel = self._assign_channel(signal_type)

        # Determine I/O type
        io_type = "Input" if signal_type in ["AI", "DI"] else "Output"

        # Get signal range
        if signal_type in ["AI", "AO"]:
            signal_range = "4-20mA DC"
        else:
            signal_range = "24VDC"

        # Determine module type
        module_type = self._get_module_type(signal_type)

        row = {
            "Tag Number": node.tag,
            "Service Description": self._get_description(node),
            "I/O Type": io_type,
            "Signal Type": signal_type,
            "Signal Range": signal_range,
            "PLC/DCS": plc_name,
            "Rack": rack,
            "Slot": slot,
            "Channel": channel,
            "Module Type": module_type,
            "Terminal": f"{signal_type}-{channel:02d}",
            "Cable Number": f"CBL-{node.tag}",
            "Junction Box": f"JB-{rack:02d}",
            "P&ID Reference": pid_reference,
            "Remarks": self._get_remarks(node),
        }

        return row

    def _assign_channel(self, signal_type: str) -> tuple[int, int, int]:
        """
        Assign rack, slot, and channel for a signal type.
        Simple auto-assignment logic.
        """
        channels_per_slot = 16
        slots_per_rack = 8

        if signal_type == "AI":
            self._ai_counter += 1
            counter = self._ai_counter
            base_slot = 1
        elif signal_type == "AO":
            self._ao_counter += 1
            counter = self._ao_counter
            base_slot = 3
        elif signal_type == "DI":
            self._di_counter += 1
            counter = self._di_counter
            base_slot = 5
        else:  # DO
            self._do_counter += 1
            counter = self._do_counter
            base_slot = 7

        # Calculate rack, slot, channel
        total_slot = base_slot + ((counter - 1) // channels_per_slot)
        rack = (total_slot - 1) // slots_per_rack + 1
        slot = ((total_slot - 1) % slots_per_rack) + 1
        channel = ((counter - 1) % channels_per_slot) + 1

        return rack, slot, channel

    def _get_module_type(self, signal_type: str) -> str:
        """Get module type name."""
        module_types = {
            "AI": "Analog Input 16Ch",
            "AO": "Analog Output 16Ch",
            "DI": "Digital Input 32Ch",
            "DO": "Digital Output 32Ch",
        }
        return module_types.get(signal_type, "Unknown")

    def _get_description(self, node) -> str:
        """Get service description."""
        if node.tag_info and node.tag_info.description:
            return node.tag_info.description
        return node.label or ""

    def _get_remarks(self, node) -> str:
        """Get remarks for the I/O point."""
        remarks = []

        if node.tag_info and node.tag_info.is_safety:
            remarks.append("SIS")

        if node.signal_info and node.signal_info.fail_safe_action:
            remarks.append(node.signal_info.fail_safe_action)

        return ", ".join(remarks)

    def to_excel(
        self,
        df: pd.DataFrame,
        output_path: str | Path,
        sheet_name: str = "I/O List",
    ) -> Path:
        """Save I/O list to Excel file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            worksheet = writer.sheets[sheet_name]

            # Set column widths
            column_widths = {
                "A": 15,  # Tag Number
                "B": 30,  # Service Description
                "C": 10,  # I/O Type
                "D": 12,  # Signal Type
                "E": 12,  # Signal Range
                "F": 12,  # PLC/DCS
                "G": 8,   # Rack
                "H": 8,   # Slot
                "I": 10,  # Channel
                "J": 20,  # Module Type
                "K": 12,  # Terminal
                "L": 15,  # Cable Number
                "M": 12,  # Junction Box
                "N": 15,  # P&ID Reference
                "O": 20,  # Remarks
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

            worksheet.freeze_panes = "A2"

        logger.info(f"Saved I/O list to: {output_path}")
        return output_path

    def get_io_summary(self, df: pd.DataFrame) -> dict:
        """Get I/O count summary."""
        summary = {
            "AI": len(df[df["Signal Type"] == "AI"]),
            "AO": len(df[df["Signal Type"] == "AO"]),
            "DI": len(df[df["Signal Type"] == "DI"]),
            "DO": len(df[df["Signal Type"] == "DO"]),
            "Total": len(df),
        }
        return summary
