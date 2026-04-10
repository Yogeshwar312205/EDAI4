"""
I/O List Generator
Auto-categorizes instruments into AI, AO, DI, DO
"""
import pandas as pd
from typing import List, Dict, Any
import re


class IOListGenerator:
    """Generate I/O List with automatic signal type classification"""
    
    # Signal type mapping based on instrument function
    SIGNAL_MAPPING = {
        # Analog Inputs (AI) - Transmitters
        'FT': ['AI'],  # Flow Transmitter
        'PT': ['AI'],  # Pressure Transmitter
        'LT': ['AI'],  # Level Transmitter
        'TT': ['AI'],  # Temperature Transmitter
        'AT': ['AI'],  # Analysis Transmitter
        'WT': ['AI'],  # Weight Transmitter
        
        # Analog Outputs (AO) - Control Valves
        'FCV': ['AO'],  # Flow Control Valve
        'PCV': ['AO'],  # Pressure Control Valve
        'LCV': ['AO'],  # Level Control Valve
        'TCV': ['AO'],  # Temperature Control Valve
        
        # Digital Inputs (DI) - Switches, Position Feedback
        'FSH': ['DI'],  # Flow Switch High
        'FSL': ['DI'],  # Flow Switch Low
        'PSH': ['DI'],  # Pressure Switch High
        'PSL': ['DI'],  # Pressure Switch Low
        'LSH': ['DI'],  # Level Switch High
        'LSL': ['DI'],  # Level Switch Low
        'TSH': ['DI'],  # Temperature Switch High
        'TSL': ['DI'],  # Temperature Switch Low
        'ZS': ['DI'],   # Position Switch
        'ZSO': ['DI'],  # Position Switch Open
        'ZSC': ['DI'],  # Position Switch Closed
        
        # Digital Outputs (DO) - On/Off Valves, Motors
        'XV': ['DO', 'DI'],  # On/Off Valve (DO for command, DI for feedback)
        'HV': ['DO', 'DI'],  # Hand Valve
        'SOV': ['DO'],       # Solenoid Valve
        'MOV': ['DO', 'DI'], # Motor Operated Valve
        
        # Controllers (may have multiple I/O)
        'FIC': ['AI', 'AO'],  # Flow Indicating Controller
        'PIC': ['AI', 'AO'],  # Pressure Indicating Controller
        'LIC': ['AI', 'AO'],  # Level Indicating Controller
        'TIC': ['AI', 'AO'],  # Temperature Indicating Controller
    }
    
    def generate(self, graph, pid_reference: str, plc_name: str) -> pd.DataFrame:
        """Generate I/O List from graph data"""
        
        io_entries = []
        
        # Get all instrument nodes
        for node in graph.get_all_nodes():
            if node.tag and self._is_instrument_tag(node.tag):
                entries = self._create_io_entries(node, pid_reference, plc_name, graph)
                io_entries.extend(entries)
        
        # Sort by I/O type, then tag
        io_entries.sort(key=lambda x: (x['I/O Type'], x['Tag Number']))
        
        # Create DataFrame
        df = pd.DataFrame(io_entries)
        
        # Reorder columns
        column_order = [
            'I/O Type',
            'Tag Number',
            'Description',
            'PLC/DCS',
            'Card/Rack',
            'Channel',
            'Signal Type',
            'Range',
            'Engineering Units',
            'Alarm Limits',
            'P&ID Drawing',
            'Cable Number',
            'Remarks'
        ]
        
        # Add missing columns
        for col in column_order:
            if col not in df.columns:
                df[col] = ''
        
        return df[column_order]
    
    def _is_instrument_tag(self, tag: str) -> bool:
        """Check if tag is an instrument tag"""
        pattern = r'^[A-Z]{2,4}[-_]?\d+'
        return bool(re.match(pattern, tag, re.IGNORECASE))
    
    def _create_io_entries(self, node, pid_reference: str, plc_name: str, graph) -> List[Dict[str, Any]]:
        """Create I/O entries for an instrument (may have multiple I/O points)"""
        
        tag = node.tag
        entries = []
        
        # Determine I/O types for this instrument
        io_types = self._determine_io_types(tag)
        
        # Create entry for each I/O type
        for idx, io_type in enumerate(io_types):
            entry = {
                'I/O Type': io_type,
                'Tag Number': tag if idx == 0 else f"{tag}_{io_type}",
                'Description': self._get_description(tag, io_type),
                'PLC/DCS': plc_name,
                'Card/Rack': self._assign_card_rack(io_type),
                'Channel': '',  # Will be assigned during detailed engineering
                'Signal Type': self._get_signal_type(io_type),
                'Range': self._get_range(tag, io_type),
                'Engineering Units': self._get_engineering_units(tag),
                'Alarm Limits': self._get_alarm_limits(tag, graph),
                'P&ID Drawing': pid_reference,
                'Cable Number': '',  # Will be assigned during installation
                'Remarks': ''
            }
            entries.append(entry)
        
        return entries
    
    def _determine_io_types(self, tag: str) -> List[str]:
        """Determine I/O types based on instrument tag"""
        
        # Extract instrument type (first 2-4 letters)
        match = re.match(r'^([A-Z]{2,4})', tag, re.IGNORECASE)
        if not match:
            return ['AI']  # Default
        
        inst_type = match.group(1).upper()
        
        # Check mapping
        if inst_type in self.SIGNAL_MAPPING:
            return self.SIGNAL_MAPPING[inst_type]
        
        # Fallback logic
        if 'T' in inst_type and inst_type.endswith('T'):
            return ['AI']  # Transmitter
        elif 'CV' in inst_type or 'V' in inst_type:
            return ['AO']  # Control Valve
        elif 'S' in inst_type:
            return ['DI']  # Switch
        else:
            return ['AI']  # Default
    
    def _get_description(self, tag: str, io_type: str) -> str:
        """Get I/O description"""
        
        descriptions = {
            'AI': 'Analog Input',
            'AO': 'Analog Output',
            'DI': 'Digital Input',
            'DO': 'Digital Output'
        }
        
        base_desc = descriptions.get(io_type, 'Unknown')
        
        # Add instrument-specific description
        if tag.startswith('F'):
            return f"{base_desc} - Flow"
        elif tag.startswith('P'):
            return f"{base_desc} - Pressure"
        elif tag.startswith('L'):
            return f"{base_desc} - Level"
        elif tag.startswith('T'):
            return f"{base_desc} - Temperature"
        else:
            return base_desc
    
    def _assign_card_rack(self, io_type: str) -> str:
        """Assign typical card/rack based on I/O type"""
        
        assignments = {
            'AI': 'AI-01',
            'AO': 'AO-01',
            'DI': 'DI-01',
            'DO': 'DO-01'
        }
        
        return assignments.get(io_type, 'TBD')
    
    def _get_signal_type(self, io_type: str) -> str:
        """Get signal type specification"""
        
        signal_types = {
            'AI': '4-20 mA',
            'AO': '4-20 mA',
            'DI': '24V DC',
            'DO': '24V DC'
        }
        
        return signal_types.get(io_type, 'TBD')
    
    def _get_range(self, tag: str, io_type: str) -> str:
        """Get typical range for instrument"""
        
        if io_type not in ['AI', 'AO']:
            return 'ON/OFF'
        
        # Typical ranges by instrument type
        if tag.startswith('F'):
            return '0-100 m³/h'
        elif tag.startswith('P'):
            return '0-10 bar'
        elif tag.startswith('L'):
            return '0-100 %'
        elif tag.startswith('T'):
            return '0-200 °C'
        else:
            return 'TBD'
    
    def _get_engineering_units(self, tag: str) -> str:
        """Get engineering units"""
        
        units = {
            'F': 'm³/h',
            'P': 'bar',
            'L': '%',
            'T': '°C',
            'W': 'kg',
            'A': 'pH'
        }
        
        first_letter = tag[0].upper() if tag else ''
        return units.get(first_letter, '')
    
    def _get_alarm_limits(self, tag: str, graph) -> str:
        """Extract alarm limits if available"""
        
        # Look for alarm tags associated with this instrument
        base_tag = re.match(r'^([A-Z]+[-_]?\d+)', tag, re.IGNORECASE)
        if not base_tag:
            return ''
        
        base = base_tag.group(1)
        alarms = []
        
        # Check for high/low alarm tags
        for node in graph.get_all_nodes():
            if node.tag:
                if f"{base}H" in node.tag.upper():
                    alarms.append('High')
                elif f"{base}L" in node.tag.upper():
                    alarms.append('Low')
                elif f"{base}HH" in node.tag.upper():
                    alarms.append('High-High')
                elif f"{base}LL" in node.tag.upper():
                    alarms.append('Low-Low')
        
        return ', '.join(alarms) if alarms else ''
