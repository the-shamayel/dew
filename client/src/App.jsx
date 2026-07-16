import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Register from './Register';
import Login from './Login';
import Events from './Events';
import EventDetails from './EventDetails';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100 font-sans">
        <nav className="bg-blue-600 text-white p-4 shadow-md">
          <div className="container mx-auto flex justify-between items-center">
            <Link to="/" className="text-xl font-bold">DEW: Decentralized Election Watch</Link>
            <div className="space-x-4">
               <Link to="/events" className="hover:underline">Events</Link>
               <Link to="/login" className="hover:underline">Login</Link>
               <Link to="/register" className="hover:underline">Register</Link>
            </div>
          </div>
        </nav>
        <main className="container mx-auto p-4 mt-8">
          <Routes>
            <Route path="/" element={
              <div className="text-center">
                <h1 className="text-4xl font-bold mb-4 text-blue-700">Welcome to DEW</h1>
                <p className="text-lg text-gray-700">Fair, Free, and Transparent Voting with Tideman Algorithm.</p>
              </div>
            } />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/events" element={<Events />} />
            <Route path="/events/:id" element={<EventDetails />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
