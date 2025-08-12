import { StreamingChatContainer } from './components/Chat/StreamingChatContainer.tsx';
// import { ChatContainer } from './components/Chat/ChatContainer.tsx';  // Non-streaming version

function App() {
  return (
    <div className="h-screen bg-gray-100 dark:bg-gray-900">
      <StreamingChatContainer />
    </div>
  );
}

export default App;