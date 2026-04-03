import { useRef,useEffect } from 'react'
import { ChatMessage } from './ChatMessage';
import './ChatMessages.css'

function ChatMessages({messageData}) {
  const chatMessageRef = useRef(null);
  useEffect(() => {
    const containerElem = chatMessageRef.current;
    if (containerElem) {
      containerElem.scrollTop = containerElem.scrollHeight;
    }
  }, [messageData]);
  return (
    <div className="chat-messages-container"
    ref={chatMessageRef}>
      {messageData.map((chat) => {
        return (
        <ChatMessage
        message={chat.message}
        sender={chat.sender}
        key={chat.id}
        />);
      })}
    </div>
  );
}

export default ChatMessages;