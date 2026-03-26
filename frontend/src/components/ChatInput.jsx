import { useState } from 'react'
import './ChatInput.css';
import LoadingImage from '../assets/loading-spinner.gif';
import api from './api';

export function ChatInput({messageData,setChatMessages}) {
  const [inputText,setInputText] = useState('');
  const [isLoading,setLoading] = useState(false);
  const [sessionId] = useState(crypto.randomUUID());
  function saveInputText(event){
    setInputText(event.target.value);
  }

  async function sendMessage() {
    if (isLoading || inputText === '') {
      return;
    }

    setInputText('');
    const newChatMessages = [
      ...messageData,
      {
        message:inputText,
        sender:'user',
        id: crypto.randomUUID()
      }
    ]
    setLoading(true);
    setChatMessages(newChatMessages);
    setChatMessages([
      ...newChatMessages,
      {
        message: <img src={LoadingImage} className="loading-spinner" />,
        sender: 'robot',
        id:crypto.randomUUID()
      }
    ]);
    setInputText('');
    try {
      const response = await api.post('/analyze',{ query: inputText,session_id: sessionId});
      const data = response.data;
      const messageText = data.summary || "No summary available.";
      
      setChatMessages([
      ...newChatMessages,
      {
        message:messageText,
        sender:'robot',
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