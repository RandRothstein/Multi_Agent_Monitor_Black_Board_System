import { useState } from 'react'
import { ChatInput } from './components/ChatInput';
import ChatMessages from './components/ChatMessages';
import './App.css'



function App() {
  const [messageData,setChatMessages] = useState([{}]);

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
