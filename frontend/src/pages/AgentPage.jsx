import { ChatInput } from '../components/ChatInput';
import ChatMessages from '../components/ChatMessages';
import { useState } from 'react';
import { Link } from 'react-router';
import './AgentPage.css'


export function AgentPage() {
    const [messageData,setChatMessages] = useState([]);

    return (
    <div className="app-container">
    <Link to="/">
    <button>Dashboard</button>
    </Link>
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