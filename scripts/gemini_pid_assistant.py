"""
Gemini P&ID Multimodal Assistant
=================================
Interactive AI assistant for querying P&ID diagrams using both visual and topological data.

Uses Gemini 2.0 Flash Exp with multimodal capabilities to answer questions about:
- Equipment locations and connections
- Pipeline tracing and flow paths
- Failure analysis and impact assessment
- Safety and operational queries

Author: AI Engineering Team
Purpose: Provide expert chemical engineering assistance for P&ID analysis
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
import google.generativeai as genai
from PIL import Image


class PIDAssistant:
    """
    Multimodal AI assistant for P&ID diagram analysis.
    Combines visual understanding with topological graph data.
    """
    
    # System prompt for the assistant
    SYSTEM_PROMPT = """You are an expert chemical engineer specializing in Piping and Instrumentation Diagrams (P&IDs).

You have access to:
1. A P&ID image showing the visual layout of equipment, pipes, valves, and instruments
2. A JSON topological graph containing:
   - nodes: List of detected equipment with their IDs, types, positions, and tags
   - edges: List of pipe connections between equipment

Your capabilities:
- Trace flow paths through the system
- Identify equipment by visual appearance or tag number
- Analyze failure scenarios and downstream impacts
- Cross-reference visual layout with connectivity data
- Provide safety and operational guidance

When answering questions:
1. Use BOTH the image and JSON data to provide complete answers
2. Reference specific equipment by their tag numbers when available
3. Trace connections using the edge data
4. Consider safety implications in failure scenarios
5. Be precise and technical in your responses

If information is missing or unclear, state what additional data would be needed."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = 'gemini-2.0-flash-exp'
    ):
        """
        Initialize the P&ID assistant.
        
        Args:
            api_key: Google API key (or set GOOGLE_API_KEY env var)
            model_name: Gemini model to use
        """
        print("=" * 70)
        print("Initializing P&ID Assistant")
        print("=" * 70)
        
        # Get API key
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key not found. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Configure Gemini
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            print(f"✓ Gemini model initialized: {model_name}")
        except Exception as e:
            print(f"✗ Failed to initialize Gemini: {e}")
            raise
        
        # Storage for current context
        self.pid_image = None
        self.topology_data = None
        self.chat_history = []
        
        print("=" * 70)
    
    def load_pid_image(self, image_path: str) -> bool:
        """
        Load P&ID image.
        
        Args:
            image_path: Path to P&ID image file
            
        Returns:
            True if successful
        """
        print(f"\n📂 Loading P&ID image: {image_path}")
        
        try:
            if not Path(image_path).exists():
                print(f"✗ Image file not found: {image_path}")
                return False
            
            self.pid_image = Image.open(image_path)
            print(f"✓ Image loaded: {self.pid_image.size[0]}x{self.pid_image.size[1]} pixels")
            return True
            
        except Exception as e:
            print(f"✗ Failed to load image: {e}")
            return False
    
    def load_topology(self, topology_path: str) -> bool:
        """
        Load topology JSON data.
        
        Args:
            topology_path: Path to topology JSON file
            
        Returns:
            True if successful
        """
        print(f"\n📂 Loading topology data: {topology_path}")
        
        try:
            if not Path(topology_path).exists():
                print(f"✗ Topology file not found: {topology_path}")
                return False
            
            with open(topology_path, 'r') as f:
                self.topology_data = json.load(f)
            
            # Print summary
            nodes = self.topology_data.get('nodes', [])
            edges = self.topology_data.get('edges', [])
            
            print(f"✓ Topology loaded:")
            print(f"  Nodes (equipment): {len(nodes)}")
            print(f"  Edges (connections): {len(edges)}")
            
            # Show sample data
            if nodes:
                print(f"\n  Sample node: {nodes[0]}")
            if edges:
                print(f"  Sample edge: {edges[0]}")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to load topology: {e}")
            return False
    
    def format_topology_for_prompt(self) -> str:
        """
        Format topology data as a readable string for the prompt.
        
        Returns:
            Formatted topology description
        """
        if not self.topology_data:
            return "No topology data available."
        
        nodes = self.topology_data.get('nodes', [])
        edges = self.topology_data.get('edges', [])
        
        # Format nodes
        nodes_text = "EQUIPMENT NODES:\n"
        for node in nodes:
            node_id = node.get('id', 'unknown')
            node_type = node.get('type', 'unknown')
            tag = node.get('tag', 'N/A')
            pos = node.get('position', {})
            
            nodes_text += f"- Node {node_id}: {node_type}"
            if tag and tag != 'N/A':
                nodes_text += f" (Tag: {tag})"
            if pos:
                nodes_text += f" at position ({pos.get('x', 0):.0f}, {pos.get('y', 0):.0f})"
            nodes_text += "\n"
        
        # Format edges
        edges_text = "\nPIPE CONNECTIONS:\n"
        for edge in edges:
            source = edge.get('source', 'unknown')
            target = edge.get('target', 'unknown')
            edge_type = edge.get('type', 'pipe')
            
            edges_text += f"- {source} → {target}"
            if edge_type != 'pipe':
                edges_text += f" ({edge_type})"
            edges_text += "\n"
        
        return f"{nodes_text}\n{edges_text}"
    
    def ask_question(self, question: str) -> str:
        """
        Ask a question about the P&ID.
        
        Args:
            question: User's question
            
        Returns:
            Assistant's response
        """
        if not self.pid_image:
            return "❌ Error: No P&ID image loaded. Please load an image first."
        
        if not self.topology_data:
            return "❌ Error: No topology data loaded. Please load topology JSON first."
        
        try:
            # Format topology data
            topology_text = self.format_topology_for_prompt()
            
            # Build the multimodal prompt
            prompt_parts = [
                self.SYSTEM_PROMPT,
                "\n\nTOPOLOGY DATA:",
                topology_text,
                "\n\nUSER QUESTION:",
                question
            ]
            
            # Combine text and image
            content = ["\n".join(prompt_parts), self.pid_image]
            
            # Generate response
            print("\n🤖 Thinking...")
            response = self.model.generate_content(content)
            
            # Extract text
            answer = response.text.strip()
            
            # Store in history
            self.chat_history.append({
                'question': question,
                'answer': answer
            })
            
            return answer
            
        except Exception as e:
            error_msg = f"❌ Error generating response: {e}"
            print(error_msg)
            return error_msg
    
    def interactive_session(self):
        """
        Start an interactive Q&A session.
        """
        print("\n" + "=" * 70)
        print("INTERACTIVE P&ID ASSISTANT")
        print("=" * 70)
        
        if not self.pid_image or not self.topology_data:
            print("\n❌ Error: Missing data!")
            print("Please load both P&ID image and topology JSON before starting.")
            return
        
        print("\nReady to answer questions about your P&ID!")
        print("\nExample questions:")
        print("  - What equipment is connected to valve FV-101?")
        print("  - If the valve on the primary cooling line fails, what happens?")
        print("  - Trace the flow path from the inlet to the reactor")
        print("  - What instruments are monitoring the pressure in the system?")
        print("  - Identify all safety valves and their locations")
        
        print("\nCommands:")
        print("  'quit' or 'exit' - End session")
        print("  'history' - Show conversation history")
        print("  'clear' - Clear conversation history")
        
        print("\n" + "=" * 70)
        
        while True:
            try:
                # Get user input
                question = input("\n💬 Your question: ").strip()
                
                # Check for commands
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if question.lower() == 'history':
                    self.show_history()
                    continue
                
                if question.lower() == 'clear':
                    self.chat_history = []
                    print("✓ History cleared")
                    continue
                
                if not question:
                    continue
                
                # Get answer
                answer = self.ask_question(question)
                
                # Print answer
                print("\n" + "=" * 70)
                print("🤖 Assistant:")
                print("=" * 70)
                print(answer)
                print("=" * 70)
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue
    
    def show_history(self):
        """Show conversation history."""
        if not self.chat_history:
            print("\n📝 No conversation history yet.")
            return
        
        print("\n" + "=" * 70)
        print("CONVERSATION HISTORY")
        print("=" * 70)
        
        for i, entry in enumerate(self.chat_history, 1):
            print(f"\n[{i}] Q: {entry['question']}")
            print(f"    A: {entry['answer'][:200]}...")
        
        print("=" * 70)
    
    def save_session(self, output_path: str):
        """
        Save conversation history to file.
        
        Args:
            output_path: Path to save JSON file
        """
        try:
            with open(output_path, 'w') as f:
                json.dump({
                    'chat_history': self.chat_history,
                    'topology_summary': {
                        'nodes': len(self.topology_data.get('nodes', [])),
                        'edges': len(self.topology_data.get('edges', []))
                    }
                }, f, indent=2)
            
            print(f"\n💾 Session saved to: {output_path}")
            
        except Exception as e:
            print(f"\n❌ Failed to save session: {e}")


def main():
    """
    Main execution function.
    """
    # Configuration
    PID_IMAGE = "data/input/pid_image.jpg"
    TOPOLOGY_JSON = "output/topology.json"
    
    print("\n" + "=" * 70)
    print("GEMINI P&ID MULTIMODAL ASSISTANT")
    print("=" * 70)
    
    try:
        # Initialize assistant
        assistant = PIDAssistant()
        
        # Load P&ID image
        if not assistant.load_pid_image(PID_IMAGE):
            print(f"\n⚠️  Could not load image: {PID_IMAGE}")
            print("Please update PID_IMAGE path in the script")
            return
        
        # Load topology data
        if not assistant.load_topology(TOPOLOGY_JSON):
            print(f"\n⚠️  Could not load topology: {TOPOLOGY_JSON}")
            print("Please update TOPOLOGY_JSON path in the script")
            print("\nOr generate topology by running your pipeline first:")
            print("  python -m src.api.main")
            return
        
        # Start interactive session
        assistant.interactive_session()
        
        # Save session
        if assistant.chat_history:
            output_file = "output/pid_assistant_session.json"
            assistant.save_session(output_file)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
