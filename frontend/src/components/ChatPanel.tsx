// Engineering Q&A Assistant - Chat Panel for P&ID Topology Questions
import React, { useState, useRef, useEffect } from 'react';
import { Panel } from 'reactflow';
import { Send, Bot, User, Loader2, MessageSquare, X, Minimize2, Maximize2 } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatPanelProps {
  nodes: any[];
  edges: any[];
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ nodes, edges }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Prepare topology data
      const topology = {
        nodes: nodes.map((node) => ({
          id: node.id,
          type: node.data?.type || 'unknown',
          tag: node.data?.label || node.id,
          label: node.data?.label || node.id,
          x: node.position.x,
          y: node.position.y,
        })),
        edges: edges.map((edge) => ({
          source: edge.source,
          target: edge.target,
          type: edge.type || 'connected_to',
        })),
      };

      // Call API
      const response = await fetch('/api/api/ask-pid', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userMessage.content,
          topology: topology,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get response');
      }

      const data = await response.json();

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.answer,
        timestamp: data.timestamp,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error asking question:', error);
      
      let errorMessage = '⚠️ Error: ';
      
      if (error instanceof Error) {
        const msg = error.message;
        
        // Check for quota exceeded
        if (msg.includes('429') || msg.includes('quota') || msg.includes('Quota exceeded')) {
          errorMessage = `🚫 API Quota Exceeded\n\nYou've reached the free tier limit for Gemini API.\n\n💡 Solutions:\n• Wait 35 seconds and try again (per-minute limit)\n• Wait until tomorrow (per-day limit resets)\n• Upgrade to paid tier for unlimited requests\n\nCheck your usage: https://ai.dev/rate-limit`;
        }
        // Check for invalid API key
        else if (msg.includes('API key') || msg.includes('401') || msg.includes('403')) {
          errorMessage = `🔑 API Key Issue\n\nPlease check your GOOGLE_API_KEY in .env file.\n\nGet a valid key: https://makersuite.google.com/app/apikey`;
        }
        // Check for model not found
        else if (msg.includes('404') && msg.includes('model')) {
          errorMessage = `🤖 Model Not Available\n\nThe Gemini model is not available. Please check backend logs for details.`;
        }
        // Generic error
        else {
          errorMessage += msg;
        }
      } else {
        errorMessage += 'Failed to process question. Please check that the Gemini API is configured correctly.';
      }
      
      const errorMessageObj: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, errorMessageObj]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
  };

  // Suggested questions
  const suggestedQuestions = [
    "What instruments are measuring flow in this P&ID?",
    "Trace the flow path from the inlet to the outlet",
    "What control loops are present in this system?",
    "List all safety instruments and their functions",
    "How are the valves connected in this process?",
  ];

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
    inputRef.current?.focus();
  };

  // Floating button when closed
  if (!isOpen) {
    return (
      <Panel position="bottom-right" className="m-4">
        <button
          onClick={() => setIsOpen(true)}
          className="bg-accent-blue hover:bg-accent-blue/90 text-white rounded-full p-4 shadow-2xl transition-all hover:scale-110 flex items-center gap-2 group"
          title="Open Engineering Q&A Assistant"
        >
          <MessageSquare className="w-6 h-6" />
          <span className="max-w-0 overflow-hidden group-hover:max-w-xs transition-all duration-300 whitespace-nowrap text-sm font-semibold">
            Ask about P&ID
          </span>
        </button>
      </Panel>
    );
  }

  return (
    <Panel position="bottom-right" className="m-4">
      <div
        className={`bg-industrial-800/98 backdrop-blur-md border-2 border-industrial-600 rounded-lg shadow-2xl transition-all ${
          isMinimized ? 'w-80' : 'w-96'
        }`}
        style={{ maxHeight: isMinimized ? '60px' : '600px' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-industrial-600 bg-industrial-900/50">
          <div className="flex items-center gap-2">
            <div className="bg-accent-blue/20 p-2 rounded-lg">
              <Bot className="w-5 h-5 text-accent-blue" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-industrial-200 font-mono">
                Engineering Q&A
              </h3>
              <p className="text-[10px] text-industrial-400">
                Powered by Gemini AI
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1.5 hover:bg-industrial-700 rounded transition-colors"
              title={isMinimized ? 'Maximize' : 'Minimize'}
            >
              {isMinimized ? (
                <Maximize2 className="w-4 h-4 text-industrial-400" />
              ) : (
                <Minimize2 className="w-4 h-4 text-industrial-400" />
              )}
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 hover:bg-industrial-700 rounded transition-colors"
              title="Close"
            >
              <X className="w-4 h-4 text-industrial-400" />
            </button>
          </div>
        </div>

        {!isMinimized && (
          <>
            {/* Messages Area */}
            <div className="h-96 overflow-y-auto p-4 space-y-3 bg-industrial-950/30">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <Bot className="w-12 h-12 text-industrial-600 mb-3" />
                  <p className="text-sm text-industrial-400 mb-4 px-4">
                    Ask me anything about this P&ID topology!
                  </p>
                  <div className="space-y-2 w-full">
                    <p className="text-xs text-industrial-500 font-semibold mb-2">
                      Try asking:
                    </p>
                    {suggestedQuestions.slice(0, 3).map((question, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSuggestedQuestion(question)}
                        className="w-full text-left text-xs text-industrial-400 hover:text-accent-blue hover:bg-industrial-800 p-2 rounded transition-colors"
                      >
                        💡 {question}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex gap-2 ${
                        message.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      {message.role === 'assistant' && (
                        <div className="flex-shrink-0 w-7 h-7 bg-accent-blue/20 rounded-full flex items-center justify-center">
                          <Bot className="w-4 h-4 text-accent-blue" />
                        </div>
                      )}
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          message.role === 'user'
                            ? 'bg-accent-blue text-white'
                            : 'bg-industrial-800 text-industrial-200 border border-industrial-700'
                        }`}
                      >
                        <p className="text-xs leading-relaxed whitespace-pre-wrap">
                          {message.content}
                        </p>
                        <p
                          className={`text-[9px] mt-1 ${
                            message.role === 'user'
                              ? 'text-white/60'
                              : 'text-industrial-500'
                          }`}
                        >
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                      {message.role === 'user' && (
                        <div className="flex-shrink-0 w-7 h-7 bg-industrial-700 rounded-full flex items-center justify-center">
                          <User className="w-4 h-4 text-industrial-300" />
                        </div>
                      )}
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex gap-2 justify-start">
                      <div className="flex-shrink-0 w-7 h-7 bg-accent-blue/20 rounded-full flex items-center justify-center">
                        <Bot className="w-4 h-4 text-accent-blue" />
                      </div>
                      <div className="bg-industrial-800 border border-industrial-700 rounded-lg p-3">
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 text-accent-blue animate-spin" />
                          <p className="text-xs text-industrial-400">
                            Analyzing topology...
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Input Area */}
            <div className="p-3 border-t border-industrial-600 bg-industrial-900/50">
              {messages.length > 0 && (
                <button
                  onClick={handleClear}
                  className="text-[10px] text-industrial-500 hover:text-accent-red mb-2 transition-colors"
                >
                  Clear conversation
                </button>
              )}
              <form onSubmit={handleSubmit} className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about the P&ID topology..."
                  disabled={isLoading}
                  className="flex-1 bg-industrial-900 border border-industrial-600 rounded-lg px-3 py-2 text-sm text-industrial-200 placeholder-industrial-500 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="bg-accent-blue hover:bg-accent-blue/90 disabled:bg-industrial-700 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 transition-colors flex items-center gap-2"
                  title="Send question"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </form>
              <p className="text-[9px] text-industrial-500 mt-2 text-center">
                {nodes.length} nodes • {edges.length} edges loaded
              </p>
            </div>
          </>
        )}
      </div>
    </Panel>
  );
};
