"""
Alarm & Trip List Generator
Extracts alarm and interlock information from P&ID
"""
import pandas as pd
from typing import List, Dict, Any
import re


class AlarmListGenerator:
    """Generate Alarm and Trip Lists"""
    
    # Alarm modifier patterns
    ALARM_PATTERNS = {
        'PAH': ('Pressure Alarm High', 'High', 'Alarm'),
        'PAL': ('Pressure Alarm Low', 'Low', 'Alarm'),
        'PAHH': ('Pressure Alarm High-High', 'High-High', 'Trip'),
        'PALL': ('Pressure Alarm Low-Low', 'Low-Low', 'Trip'),
        'LAH': ('Level Alarm High', 'High', 'Alarm'),
        'LAL': ('Level Alarm Low', 'Low', 'Alarm'),
        'LAHH': ('Level Alarm High-High', 'High-High', 'Trip'),
        'LALL': ('Level Alarm Low-Low', 'Low-Low', 'Trip'),
        'TAH': ('Temperature Alarm High', 'High', 'Alarm'),
        'TAL': ('Temperature Alarm Low', 'Low', 'Alarm'),
        'TAHH': ('Temperature Alarm High-High', 'High-High', 'Trip'),
        'TALL': ('Temperature Alarm Low-Low', 'Low-Low', 'Trip'),
        'FAH': ('Flow Alarm High', 'High', 'Alarm'),
        'FAL': ('Flow Alarm Low', 'Low', 'Alarm'),
        'FAHH': ('Flow Alarm High-High', 'High-High', 'Trip'),
        'FALL': ('Flow Alarm Low-Low', 'Low-Low', 'Trip'),
        'PSH': ('Pressure Switch High', 'High', 'Interlock'),
        'PSL': ('Pressure Switch Low', 'Low', 'Interlock'),
        'LSH': ('Level Switch High', 'High', 'Interlock'),
        'LSL': ('Level Switch Low', 'Low', 'Interlock'),
        'TSH': ('Temperature Switch High', 'High', 'Interlock'),
        'TSL': ('Temperature Switch Low', 'Low', 'Interlock'),
        'FSH': ('Flow Switch High', 'High', 'Interlock'),
        'FSL': ('Flow Switch Low', 'Low', 'Interlock'),
    }
    
    def generate(self, graph, pid_reference: str) -> pd.DataFrame:
        """Generate Alarm and Trip List"""
        
        alarms = []
        
        # Scan all nodes for alarm/trip tags
        for node in graph.get_all_nodes():
            if node.tag:
                alarm_data = self._extract_alarm_data(node, pid_reference, graph)
                if alarm_data:
                    alarms.append(alarm_data)
        
        # Sort by priority (Trip > Alarm), then by tag
        alarms.sort(key=lambda x: (
            0 if x['Type'] == 'Trip' else 1 if x['Type'] == 'Interlock' else 2,
            x['Tag Number']
        ))
        
        # Create DataFrame
        df = pd.DataFrame(alarms)
        
        if df.empty:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=[
                'Tag Number',
                'Description',
                'Type',
                'Setpoint',
                'Limit Type',
                'Action',
                'Consequence',
                'Priority',
                'Associated Equipment',
                'P&ID Drawing',
                'Safety Critical',
                'Remarks'
            ])
        
        # Reorder columns
        column_order = [
            'Tag Number',
            'Description',
            'Type',
            'Setpoint',
            'Limit Type',
            'Action',
            'Consequence',
            'Priority',
            'Associated Equipment',
            'P&ID Drawing',
            'Safety Critical',
            'Remarks'
        ]
        
        # Add missing columns
        for col in column_order:
            if col not in df.columns:
                df[col] = ''
        
        return df[column_order]
    
    def _extract_alarm_data(self, node, pid_reference: str, graph) -> Dict[str, Any]:
        """Extract alarm/trip data from node"""
        
        tag = node.tag.upper()
        
        # Check if tag matches alarm pattern
        alarm_info = None
        for pattern, info in self.ALARM_PATTERNS.items():
            if pattern in tag:
                alarm_info = info
                break
        
        if not alarm_info:
            return None
        
        description, limit_type, alarm_type = alarm_info
        
        # Determine priority
        priority = self._determine_priority(alarm_type, limit_type)
        
        # Find associated equipment
        equipment = self._find_associated_equipment(node, graph)
        
        # Determine action
        action = self._determine_action(alarm_type, limit_type)
        
        # Determine consequence
        consequence = self._determine_consequence(alarm_type, equipment)
        
        # Check if safety critical
        safety_critical = 'Yes' if alarm_type in ['Trip', 'Interlock'] else 'No'
        
        return {
            'Tag Number': node.tag,
            'Description': description,
            'Type': alarm_type,
            'Setpoint': self._get_typical_setpoint(tag, limit_type),
            'Limit Type': limit_type,
            'Action': action,
            'Consequence': consequence,
            'Priority': priority,
            'Associated Equipment': equipment,
            'P&ID Drawing': pid_reference,
            'Safety Critical': safety_critical,
            'Remarks': ''
        }
    
    def _determine_priority(self, alarm_type: str, limit_type: str) -> str:
        """Determine alarm priority"""
        
        if alarm_type == 'Trip':
            return 'Critical'
        elif alarm_type == 'Interlock':
            return 'High'
        elif 'High-High' in limit_type or 'Low-Low' in limit_type:
            return 'High'
        else:
            return 'Medium'
    
    def _find_associated_equipment(self, node, graph) -> str:
        """Find equipment associated with alarm"""
        
        equipment = []
        
        # Look for connected equipment nodes
        for edge in graph.get_edges_from_node(node.id):
            target_node = graph.get_node(edge.target_id)
            if target_node and target_node.node_type.value in ['equipment', 'pump', 'vessel', 'tank']:
                if target_node.tag:
                    equipment.append(target_node.tag)
        
        # Also check incoming edges
        for edge in graph.get_edges_to_node(node.id):
            source_node = graph.get_node(edge.source_id)
            if source_node and source_node.node_type.value in ['equipment', 'pump', 'vessel', 'tank']:
                if source_node.tag:
                    equipment.append(source_node.tag)
        
        return ', '.join(equipment) if equipment else 'TBD'
    
    def _determine_action(self, alarm_type: str, limit_type: str) -> str:
        """Determine alarm action"""
        
        if alarm_type == 'Trip':
            return 'Shutdown equipment'
        elif alarm_type == 'Interlock':
            if 'High' in limit_type:
                return 'Close inlet valve'
            else:
                return 'Open bypass valve'
        else:
            return 'Operator notification'
    
    def _determine_consequence(self, alarm_type: str, equipment: str) -> str:
        """Determine consequence of alarm"""
        
        if alarm_type == 'Trip':
            return f'Emergency shutdown of {equipment if equipment != "TBD" else "system"}'
        elif alarm_type == 'Interlock':
            return 'Automatic protective action'
        else:
            return 'Operator intervention required'
    
    def _get_typical_setpoint(self, tag: str, limit_type: str) -> str:
        """Get typical setpoint value"""
        
        # This would ideally come from engineering data
        # For now, return placeholder
        
        if 'P' in tag:  # Pressure
            if 'High' in limit_type:
                return '10 bar'
            else:
                return '2 bar'
        elif 'L' in tag:  # Level
            if 'High' in limit_type:
                return '90%'
            else:
                return '10%'
        elif 'T' in tag:  # Temperature
            if 'High' in limit_type:
                return '150°C'
            else:
                return '10°C'
        elif 'F' in tag:  # Flow
            if 'High' in limit_type:
                return '100 m³/h'
            else:
                return '10 m³/h'
        
        return 'TBD'
