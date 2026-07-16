import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function Events() {
  const [events, setEvents] = useState([]);
  const [eventName, setEventName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const res = await fetch('/api/events');
      const data = await res.json();
      if (res.ok) setEvents(data.events);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ eventName, password })
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to create event");
      } else {
        setEventName('');
        setPassword('');
        fetchEvents();
      }
    } catch (err) {
      setError("Network error");
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold mb-6 text-gray-800">Voting Events</h2>

      <div className="bg-white p-6 border rounded-lg shadow-sm mb-8">
        <h3 className="text-xl font-semibold mb-4">Create New Event</h3>
        {error && <div className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</div>}
        <form onSubmit={handleCreateEvent} className="flex space-x-4 items-end">
          <div className="flex-1">
            <label className="block text-gray-700 mb-1">Event Name</label>
            <input type="text" value={eventName} onChange={e => setEventName(e.target.value)}
                   className="w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500" required />
          </div>
          <div className="flex-1">
            <label className="block text-gray-700 mb-1">Event Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                   className="w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500" required />
          </div>
          <button type="submit" className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 h-[42px]">Create</button>
        </form>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {events.map(ev => (
          <div key={ev.id} className="bg-white p-6 border rounded-lg shadow-sm flex justify-between items-center">
            <div>
              <h4 className="text-lg font-semibold">{ev.name}</h4>
              <p className="text-sm text-gray-500">Created: {ev.date}</p>
            </div>
            <Link to={`/events/${ev.id}`} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition">
              Join / View
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Events;
