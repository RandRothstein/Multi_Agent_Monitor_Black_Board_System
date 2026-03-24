import { useState } from 'react'
import { Chatbot } from 'supersimpledev';
import './ChatInput.css';
import api from './api';

export function ChatInput({messageData,setChatMessages}) {
  const [inputText,setInputText] = useState('');
  const [isLoading,setLoading] = useState(false);
  function saveInputText(event){
    setInputText(event.target.value);
  }

  async function sendMessage() {
    if (isLoading || inputText === '') {
      return;
    }

    setInputText('');
    setLoading(true);
    const newChatMessages = [
      ...messageData,
      {
        message:inputText,
        sender:'user',
        id: crypto.randomUUID()
      }
    ]
    setChatMessages(newChatMessages);
    setChatMessages([
      ...newChatMessages,
      {
        message:'Loading...',
        sender: 'robot',
        id:crypto.randomUUID()
      }
    ]);
    setInputText('');
    try {
      const response = await api.post('/analyze',{ query: inputText});
      const data = response.data;
      const messageText = data.summary || "No summary available.";
          setChatMessages([
      ...newChatMessages,
      {
        message:messageText,
        sender:'robat',
        id: crypto.randomUUID()
      }
    ]);
    } catch (error) {
      console.log('Backend Error:',error);
    } finally{
      setLoading(false);
    }
  }




  function handleKeyDown() {
    if (event.key === 'Enter'){
      sendMessage();
    }
    else if (event.key === 'Escape'){
      setInputText('');            }
  }
  return (
    <div className="chat-input-container">
      <input className="chat-input" placeholder="Send a message to Chatbot" size="30" 
      onChange={saveInputText} onKeyDown={handleKeyDown} value={inputText}
      />
      <button onClick={sendMessage} className="send-button">Send</button>
    </div>
  );
}