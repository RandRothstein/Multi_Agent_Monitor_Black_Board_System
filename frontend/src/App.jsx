import { useState } from 'react'
import { ChatInput } from './components/ChatInput';
import ChatMessages from './components/ChatMessages';
import './App.css'



function App() {
  const [messageData,setChatMessages] = useState([{
    message:'hello chatbot',
    sender: 'user',
    id: 'id1'
  },
  {
    message: 'Hello! How can I help you?',
    sender: 'robat',
    id: 'id2'
  },
  {
    message: 'can you get me todays date?',
    sender: 'user',
    id: 'id3'
  },
  {
    message: 'Today is August 17',
    sender: 'robat',
    id: 'id4'
  }
  ]
);

  return (
  <div className="app-container"> 
    <ChatMessages messageData ={messageData}/>
    <ChatInput 
    messageData={messageData}
    setChatMessages={setChatMessages}/>
  </div>
  );
}

export default App
