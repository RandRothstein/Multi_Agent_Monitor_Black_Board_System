import { Routes, Route } from 'react-router';
import { AgentPage } from './pages/AgentPage';
import { HomePage } from './pages/HomePage';
import './App.css'



function App() {
  return (
    <Routes>
      <Route index element={<HomePage />} />
      <Route path="chat" element={<AgentPage />} />
    </Routes>
  );
}

export default App
