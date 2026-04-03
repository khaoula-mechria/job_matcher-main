import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import PostJob from './component/PostJob';
import GetJob from './component/GetJob';
import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <Router>
      <Routes>
        <Route path="/" element={<PostJob />} />
        <Route path="/GetJobs" element={<GetJob />} />
      </Routes>
    </Router>
  );
}

export default App;
