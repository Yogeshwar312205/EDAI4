"""
Instrument Index Generator
Extracts comprehensive instrument data from P&ID
"""
import pandas as pd
from typing import List, Dict, Any
import re


class InstrumentIndexGenerator:
    """Generate professional Instrument Index"""
    
    # ISA instrument type mapping
    INSTRUMENT_TYPES = {
        'F': 'Flow',
        'P': 'Pressure',
        'L': 'Level',
        'T': 'Temperature',
        'A': 'Analysis',
        'S': 'Speed',
        'V': 'Vibration',
        'W': 'Weight',
        'Q': 'Quality',
    }
    
    FUNCTION_TYPES = {
        'T': 'Transmitter',
        'I': 'Indicator',
        'C': 'Controller',
        'R': 'Recorder',
        'A': 'Alarm',
        'S': 'Switch',
        'V': 'Valve',
        'E': 'Element',
        'Y': 'Relay',
        'Z': 'Position',
    }
    
    def generate(self, graph, pid_reference: str) -> pd.DataFrame:
        """Generate Instrument Index from graph data"""
        
        instruments = []
        
        # Get all instrument nodes from graph
        for node in graph.get_all_nodes():
            if node.tag and self._is_instrument_tag(node.tag):
                instrument_data = self._extract_instrument_data(node, pid_reference, graph)
                instruments.append(instrument_data)
        
        # Sort by tag number
        instruments.sort(key=lambda x: x['Tag Number'])
        
        # Create DataFrame
        df = pd.DataFrame(instruments)
        
        # Reorder columns
        column_order = [
            'Tag Number',
            'Instrument Type',
            'Measured Variable',
            'Function',
            'Service Description',
            'P&ID Drawing',
            'Location',
            'Connected Equipment',
            'Line Number',
            'Remarks'
        ]
        
        # Add missing columns
        for col in column_order:
            if col not in df.columns:
                df[col] = ''
        
        return df[column_order]
    
    def _is_instrument_tag(self, tag: str) -> bool:
        """Check if tag is an instrument tag"""
        # ISA format: XX-###
        pattern = r'^[A-Z]{2,4}[-_]?\d+'
        return bool(re.match(pattern, tag, re.IGNORECASE))
    
    def _extract_instrument_data(self, node, pid_reference: str, graph) -> Dict[str, Any]:
        """Extract detailed instrument information"""
        
        tag = node.tag
        
        # Parse ISA tag
        first_letter = tag[0].upper() if tag else ''
        second_letter = tag[1].upper() if len(tag) > 1 else ''
        
        measured_var = self.INSTRUMENT_TYPES.get(first_letter, 'Unknown')
        function = self.FUNCTION_TYPES.get(second_letter, 'Unknown')
        
        # Determine instrument type
        instrument_type = f"{measured_var} {function}"
        
        # Get service description from context
        service_desc = self._infer_service_description(tag, measured_var, function)
        
        # Find connected equipment
        connected_equipment = self._find_connected_equipment(node, graph)
        
        # Find line number
        line_number = self._find_line_number(node, graph)
        
        # Determine location (from spatial data if available)
        location = self._determine_location(node)
        
        return {
            'Tag Number': tag,
            'Instrument Type': instrument_type,
            'Measured Variable': measured_var,
            'Function': function,
            'Service Description': service_desc,
            'P&ID Drawing': pid_reference,
            'Location': location,
            'Connected Equipment': connected_equipment,
            'Line Number': line_number,
            'Remarks': ''
        }
    
    def _infer_service_description(self, tag: str, measured_var: str, function: str) -> str:
        """Infer service description from tag and type"""
        
        descriptions = {
            'Flow Transmitter': 'Flow measurement and transmission',
            'Pressure Transmitter': 'Pressure measurement and transmission',
            'Level Transmitter': 'Level measurement and transmission',
            'Temperature Transmitter': 'Temperature measurement and transmission',
            'Flow Indicator': 'Local flow indication',
            'Pressure Indicator': 'Local pressure indication',
            'Level Indicator': 'Local level indication',
            'Temperature Indicator': 'Local temperature indication',
            'Flow Controller': 'Flow control',
            'Pressure Controller': 'Pressure control',
            'Level Controller': 'Level control',
            'Temperature Controller': 'Temperature control',
            'Pressure Alarm': 'Pressure alarm monitoring',
            'Level Alarm': 'Level alarm monitoring',
            'Temperature Alarm': 'Temperature alarm monitoring',
            'Control Valve': 'Flow control valve',
            'Pressure Switch': 'Pressure switch',
            'Level Switch': 'Level switch',
        }
        
        key = f"{measured_var} {function}"
        return descriptions.get(key, f"{measured_var} {function}")
    
    def _find_connected_equipment(self, node, graph) -> str:
        """Find equipment connected to this instrument"""
        
        # Look for edges connecting to equipment nodes
        connected = []
        
        for edge in graph.get_edges_from_node(node.id):
            target_node = graph.get_node(edge.target_id)
            if target_node and target_node.node_type.value in ['equipment', 'pump', 'vessel', 'tank']:
                if target_node.tag:
                    connected.append(target_node.tag)
        
        return ', '.join(connected) if connected else ''
    
    def _find_line_number(self, node, graph) -> str:
        """Find line number associated with instrument"""
        
        # Look for line nodes connected to this instrument
        for edge in graph.get_edges_from_node(node.id):
            target_node = graph.get_node(edge.target_id)
            if target_node and target_node.node_type.value == 'line':
                if target_node.tag:
                    return target_node.tag
        
        return ''
    
    def _determine_location(self, node) -> str:
        """Determine instrument location"""
        
        # Could be enhanced with spatial clustering
        if hasattr(node, 'x') and hasattr(node, 'y'):
            # Simple quadrant-based location
            if node.x < 500:
                h_pos = 'Left'
            elif node.x < 1000:
                h_pos = 'Center'
            else:
                h_pos = 'Right'
            
            if node.y < 400:
                v_pos = 'Top'
            elif node.y < 800:
                v_pos = 'Middle'
            else:
                v_pos = 'Bottom'
            
            return f"{v_pos}-{h_pos}"
        
        return 'Field'
