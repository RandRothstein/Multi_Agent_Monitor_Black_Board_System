import { useState } from 'react'
import { ChatInput } from './components/ChatInput';
import ChatMessages from './components/ChatMessages';
import './App.css'



function App() {
  const [messageData,setChatMessages] = useState([]);
  return (
  <div className="app-container"> 
    <ChatMessages messageData ={messageData}/>
    {messageData.length === 0 && (
      <h2 className="welcome-message"> Welcome to Saul. I'm here to answer your business questions. Let’s get started.</h2>
    )}
    <ChatInput 
    messageData={messageData}
    setChatMessages={setChatMessages}/>
  </div>
  );
}

export default App
