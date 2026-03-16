import { useChatStore } from '@/stores/chatStore'

export function App() {
  const { messages, isLoading, department, sessionId } = useChatStore()

  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar placeholder */}
      <aside className="w-64 border-r border-gray-200 bg-gray-50 p-4">
        <div className="mb-4">
          <h1 className="text-lg font-semibold">Multi-Agent RAG</h1>
          <p className="text-sm text-gray-600">Chat Interface</p>
        </div>
        <div className="space-y-2">
          <div className="text-sm">
            <span className="text-gray-600">Department:</span>
            <span className="ml-2 font-medium">{department}</span>
          </div>
          <div className="text-sm">
            <span className="text-gray-600">Session:</span>
            <span className="ml-2 font-mono text-xs">{sessionId || 'N/A'}</span>
          </div>
          <div className="text-sm">
            <span className="text-gray-600">Messages:</span>
            <span className="ml-2 font-medium">{messages.length}</span>
          </div>
        </div>
      </aside>

      {/* Main content area */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="border-b border-gray-200 bg-white px-6 py-4">
          <h2 className="text-xl font-semibold">Chat</h2>
        </header>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto p-6">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-400">No messages yet. Start a conversation.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-md rounded-lg px-4 py-2 ${
                      msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-900'
                    }`}
                  >
                    <p>{msg.content}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Input area */}
        <footer className="border-t border-gray-200 bg-white px-6 py-4">
          {isLoading ? (
            <div className="text-center text-gray-500 text-sm">Loading...</div>
          ) : (
            <p className="text-gray-500 text-sm">Chat input component placeholder</p>
          )}
        </footer>
      </main>
    </div>
  )
}

export default App
