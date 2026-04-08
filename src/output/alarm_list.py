"""
EDAI4 - Alarm List Generator
Generates Alarm List deliverable from P&ID graph
"""

from pathlib import Path
import pandas as pd

from src.utils import get_logger
from src.topology import PIDGraph

logger = get_logger(__name__)


class AlarmListGenerator:
    """
    Generates Alarm List from P&ID graph.

    The Alarm List catalogs all process alarms with setpoints,
    priorities, and response actions.
    """

    # Column definitions for alarm list
    COLUMNS = [
        "Tag Number",
        "Service Description",
        "Alarm Type",
        "Measured Variable",
        "Setpoint",
        "Unit",
        "Priority",
        "Response Action",
        "Consequence",
        "P&ID Reference",
        "Remarks",
    ]

    # Priority mapping based on alarm type
    PRIORITY_MAP = {
        "High-High": "Critical",
        "Low-Low": "Critical",
        "High": "High",
        "Low": "High",
        "Alarm": "Medium",
    }

    def __init__(self):
        """Initialize alarm list generator."""
        logger.info("AlarmListGenerator initialized")

    def generate(
        self,
        graph: PIDGraph,
        pid_reference: str = "",
    ) -> pd.DataFrame:
        """
        Generate alarm list from P&ID graph.

        Args:
            graph: PIDGraph with instrument nodes
            pid_reference: P&ID drawing reference number

        Returns:
            DataFrame with alarm list data
        """
        data = []

        for node in graph.get_tagged_nodes():
            # Check if this is an alarm/switch instrument
            if not node.tag_info:
                continue

            if not node.tag_info.has_alarm:
                continue

            row = {
                "Tag Number": node.tag,
                "Service Description": self._get_description(node),
                "Alarm Type": self._get_alarm_type(node),
                "Measured Variable": self._get_measured_variable(node),
                "Setpoint": self._get_setpoint(node),
                "Unit": self._get_unit(node),
                "Priority": self._get_priority(node),
                "Response Action": self._get_response_action(node),
                "Consequence": self._get_consequence(node),
                "P&ID Reference": pid_reference,
                "Remarks": self._get_remarks(node),
            }

            data.append(row)

        df = pd.DataFrame(data, columns=self.COLUMNS)
        df = df.sort_values(["Priority", "Tag Number"]).reset_index(drop=True)

        logger.info(f"Generated alarm list: {len(df)} alarms")
        return df

    def _get_description(self, node) -> str:
        """Get alarm description."""
        if node.tag_info and node.tag_info.description:
            return node.tag_info.description
        return node.label or ""

    def _get_alarm_type(self, node) -> str:
        """Get alarm type (High, Low, High-High, etc.)."""
        if node.tag_info and node.tag_info.alarm_type:
            return node.tag_info.alarm_type
        return ""

    def _get_measured_variable(self, node) -> str:
        """Get measured variable."""
        if node.tag_info and node.tag_info.measured_variable_name:
            return node.tag_info.measured_variable_name
        return ""

    def _get_setpoint(self, node) -> str:
        """Get alarm setpoint (TBD for now)."""
        return "TBD"

    def _get_unit(self, node) -> str:
        """Get engineering unit."""
        if node.tag_info and node.tag_info.unit:
            return node.tag_info.unit
        return ""

    def _get_priority(self, node) -> str:
        """Get alarm priority."""
        alarm_type = self._get_alarm_type(node)
        return self.PRIORITY_MAP.get(alarm_type, "Medium")

    def _get_response_action(self, node) -> str:
        """Get recommended response action."""
        alarm_type = self._get_alarm_type(node)
        variable = self._get_measured_variable(node)

        if "High-High" in alarm_type or "Low-Low" in alarm_type:
            return f"Investigate {variable.lower()} immediately. Check field instrument."

        if "High" in alarm_type:
            return f"Monitor {variable.lower()}. Prepare for intervention."

        if "Low" in alarm_type:
            return f"Monitor {variable.lower()}. Prepare for intervention."

        return "Acknowledge and investigate"

    def _get_consequence(self, node) -> str:
        """Get potential consequence of alarm condition."""
        alarm_type = self._get_alarm_type(node)

        if node.tag_info and node.tag_info.is_safety:
            if "High-High" in alarm_type or "Low-Low" in alarm_type:
                return "Process shutdown / Trip"
            return "Safety concern"

        if "High-High" in alarm_type or "Low-Low" in alarm_type:
            return "Equipment protection trip"

        return "Process deviation"

    def _get_remarks(self, node) -> str:
        """Get remarks."""
        remarks = []

        if node.tag_info and node.tag_info.is_safety:
            remarks.append("SIS Related")

        return ", ".join(remarks)

    def to_excel(
        self,
        df: pd.DataFrame,
        output_path: str | Path,
        sheet_name: str = "Alarm List",
    ) -> Path:
        """Save alarm list to Excel file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            worksheet = writer.sheets[sheet_name]

            column_widths = {
                "A": 15,  # Tag Number
                "B": 30,  # Service Description
                "C": 12,  # Alarm Type
                "D": 18,  # Measured Variable
                "E": 12,  # Setpoint
                "F": 10,  # Unit
                "G": 10,  # Priority
                "H": 40,  # Response Action
                "I": 25,  # Consequence
                "J": 15,  # P&ID Reference
                "K": 20,  # Remarks
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

            worksheet.freeze_panes = "A2"

        logger.info(f"Saved alarm list to: {output_path}")
        return output_path

    def get_alarm_summary(self, df: pd.DataFrame) -> dict:
        """Get alarm count by priority."""
        summary = df.groupby("Priority").size().to_dict()
        summary["Total"] = len(df)
        return summary
