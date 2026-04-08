"""
EDAI4 - Cause & Effect Matrix Generator
Generates Cause & Effect Matrix (Trip List) from P&ID graph
"""

from pathlib import Path
from typing import Optional
import pandas as pd

from src.utils import get_logger
from src.topology import PIDGraph
from src.deterministic import SafetyValidator

logger = get_logger(__name__)


class CauseEffectMatrixGenerator:
    """
    Generates Cause & Effect Matrix (C&E) from P&ID graph.

    The C&E Matrix maps trip initiators (causes) to final elements (effects),
    showing the safety logic for process shutdown systems.
    """

    # Logic symbols for C&E matrix
    LOGIC_SYMBOLS = {
        "action": "X",      # Action taken
        "no_action": "",    # No action
        "time_delay": "T",  # Time delayed
        "latched": "L",     # Latched action
        "permissive": "P",  # Permissive
    }

    def __init__(self):
        """Initialize C&E matrix generator."""
        self.safety_validator = SafetyValidator()
        logger.info("CauseEffectMatrixGenerator initialized")

    def generate(
        self,
        graph: PIDGraph,
        pid_reference: str = "",
    ) -> pd.DataFrame:
        """
        Generate Cause & Effect matrix from P&ID graph.

        Args:
            graph: PIDGraph with safety instruments
            pid_reference: P&ID drawing reference number

        Returns:
            DataFrame with C&E matrix data
        """
        # Identify causes (trip initiators) and effects (final elements)
        causes = []
        effects = []

        for node in graph.get_tagged_nodes():
            if not node.tag:
                continue

            role = self.safety_validator.get_cause_effect_role(node.tag)

            if role == "Cause":
                causes.append(node)
            elif role == "Effect":
                effects.append(node)

        if not causes or not effects:
            logger.warning("No causes or effects found for C&E matrix")
            return self._create_empty_matrix()

        # Build matrix
        matrix_data = self._build_matrix(causes, effects, pid_reference)

        logger.info(f"Generated C&E matrix: {len(causes)} causes, {len(effects)} effects")
        return matrix_data

    def _build_matrix(
        self,
        causes: list,
        effects: list,
        pid_reference: str,
    ) -> pd.DataFrame:
        """Build the C&E matrix DataFrame."""
        # Create columns: Cause info + Effect columns
        columns = [
            "Tag Number",
            "Description",
            "Trip Type",
            "P&ID Reference",
        ]

        # Add effect column names
        effect_tags = [e.tag for e in effects]
        columns.extend(effect_tags)

        # Create rows
        data = []

        for cause in causes:
            row = {
                "Tag Number": cause.tag,
                "Description": self._get_description(cause),
                "Trip Type": self._get_trip_type(cause),
                "P&ID Reference": pid_reference,
            }

            # Determine actions for each effect
            for effect in effects:
                action = self._determine_action(cause, effect)
                row[effect.tag] = action

            data.append(row)

        return pd.DataFrame(data, columns=columns)

    def _get_description(self, node) -> str:
        """Get cause/effect description."""
        if node.tag_info and node.tag_info.description:
            return node.tag_info.description
        return node.label or ""

    def _get_trip_type(self, node) -> str:
        """Get trip type (High-High, Low-Low, etc.)."""
        trip_type = self.safety_validator.get_trip_type(node.tag)
        return trip_type or ""

    def _determine_action(self, cause, effect) -> str:
        """
        Determine the action between a cause and effect.

        This is a simplified logic - in reality, this would come from
        the actual safety logic or be determined by the LLM.
        """
        # Simple heuristic: same first letter = related
        cause_tag = cause.tag.upper()
        effect_tag = effect.tag.upper()

        # Extract first letter of tag (measured variable)
        cause_var = ""
        effect_var = ""

        if cause.tag_info and cause.tag_info.first_letter:
            cause_var = cause.tag_info.first_letter

        # Check for logical relationships
        # High-High/Low-Low typically act on shutdown valves
        if "SDV" in effect_tag or "XV" in effect_tag:
            if "HH" in cause_tag or "LL" in cause_tag:
                return self.LOGIC_SYMBOLS["action"]

        # BDV (blowdown) typically triggered by pressure high-high
        if "BDV" in effect_tag:
            if "PSHH" in cause_tag or "PAHH" in cause_tag:
                return self.LOGIC_SYMBOLS["action"]

        # Default: no automatic action
        return self.LOGIC_SYMBOLS["no_action"]

    def _create_empty_matrix(self) -> pd.DataFrame:
        """Create empty C&E matrix."""
        columns = [
            "Tag Number",
            "Description",
            "Trip Type",
            "P&ID Reference",
        ]
        return pd.DataFrame(columns=columns)

    def to_excel(
        self,
        df: pd.DataFrame,
        output_path: str | Path,
        sheet_name: str = "Cause & Effect Matrix",
    ) -> Path:
        """Save C&E matrix to Excel file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            worksheet = writer.sheets[sheet_name]

            # Set column widths
            worksheet.column_dimensions["A"].width = 15  # Tag Number
            worksheet.column_dimensions["B"].width = 30  # Description
            worksheet.column_dimensions["C"].width = 12  # Trip Type
            worksheet.column_dimensions["D"].width = 15  # P&ID Reference

            # Effect columns
            from openpyxl.utils import get_column_letter
            for i in range(5, len(df.columns) + 1):
                col_letter = get_column_letter(i)
                worksheet.column_dimensions[col_letter].width = 10

            worksheet.freeze_panes = "E2"

            # Add legend
            legend_row = len(df) + 3
            worksheet.cell(row=legend_row, column=1, value="Legend:")
            worksheet.cell(row=legend_row + 1, column=1, value="X = Action taken")
            worksheet.cell(row=legend_row + 2, column=1, value="T = Time delayed")
            worksheet.cell(row=legend_row + 3, column=1, value="L = Latched")
            worksheet.cell(row=legend_row + 4, column=1, value="P = Permissive")

        logger.info(f"Saved C&E matrix to: {output_path}")
        return output_path

    def generate_trip_list(
        self,
        graph: PIDGraph,
        pid_reference: str = "",
    ) -> pd.DataFrame:
        """
        Generate simplified Trip List (flattened C&E).

        This is an alternative format showing cause-effect pairs.
        """
        data = []

        for node in graph.get_tagged_nodes():
            if not node.tag:
                continue

            if not self.safety_validator.is_sis_instrument(node.tag):
                continue

            validation = self.safety_validator.validate(node.tag_info)

            row = {
                "Tag Number": node.tag,
                "Description": self._get_description(node),
                "Role": validation.cause_or_effect or "Unknown",
                "Trip Type": validation.trip_type or "",
                "Safety Function": validation.safety_function.value,
                "SIL Level": validation.sil_level.name if validation.sil_level else "",
                "P&ID Reference": pid_reference,
            }

            data.append(row)

        columns = [
            "Tag Number",
            "Description",
            "Role",
            "Trip Type",
            "Safety Function",
            "SIL Level",
            "P&ID Reference",
        ]

        return pd.DataFrame(data, columns=columns)
