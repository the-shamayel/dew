import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function EventDetails() {
  const { id } = useParams();
  const [eventData, setEventData] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [joinPassword, setJoinPassword] = useState('');
  const [isJoined, setIsJoined] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [hasVoted, setHasVoted] = useState(false);
  const [result, setResult] = useState(null);

  const [pref1, setPref1] = useState('');
  const [pref2, setPref2] = useState('');
  const [pref3, setPref3] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    fetchEventDetails();
  }, [id]);

  const fetchEventDetails = async () => {
    try {
      const res = await fetch(`/api/dew/${id}`);
      if (res.status === 403) {
        setIsJoined(false);
      } else if (res.ok) {
        const data = await res.json();
        setEventData(data.event);
        setParticipants(data.participants);
        setHasVoted(data.has_voted);
        setIsJoined(true);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleJoin = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await fetch(`/api/dew/${id}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: joinPassword })
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to join event");
      } else {
        fetchEventDetails();
      }
    } catch (err) {
      setError("Network error");
    }
  };

  const handleVote = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`/api/dew/${id}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ select1: pref1, select2: pref2, select3: pref3 })
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to submit vote");
      } else {
        setSuccess("Vote submitted successfully!");
        setHasVoted(true);
      }
    } catch (err) {
      setError("Network error");
    }
  };

  const handlePublishResults = async () => {
    setError(null);
    try {
      const res = await fetch(`/api/result/${id}`);
      const data = await res.json();
      if (res.ok) {
        setResult(data.winner);
      } else {
        setError(data.error || "Failed to fetch results");
      }
    } catch (err) {
      setError("Network error");
    }
  };

  if (!isJoined) {
    return (
      <div className="max-w-md mx-auto bg-white p-8 border rounded-lg shadow-sm">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Join Event</h2>
        {error && <div className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</div>}
        <form onSubmit={handleJoin} className="space-y-4">
          <div>
            <label className="block text-gray-700 mb-1">Event Password</label>
            <input type="password" value={joinPassword} onChange={e => setJoinPassword(e.target.value)}
                   className="w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500" required />
          </div>
          <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition">Join</button>
        </form>
      </div>
    );
  }

  if (!eventData) return <div>Loading...</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex justify-between items-center border-b pb-4">
         <h2 className="text-3xl font-bold text-gray-800">Event: {eventData.name}</h2>
         <button onClick={handlePublishResults} className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700">
           Publish Results
         </button>
      </div>

      {result && (
        <div className="bg-green-100 border-l-4 border-green-500 p-4">
          <p className="text-xl font-bold text-green-700">Winner: {result}</p>
        </div>
      )}

      {error && <div className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</div>}
      {success && <div className="bg-green-100 text-green-700 p-3 rounded mb-4">{success}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-white p-6 border rounded-lg shadow-sm">
          <h3 className="text-xl font-semibold mb-4 border-b pb-2">Participants</h3>
          <ul className="space-y-2">
            {participants.map(p => (
              <li key={p.id} className="text-gray-700 bg-gray-50 px-3 py-2 rounded border">{p.username}</li>
            ))}
          </ul>
        </div>

        <div className="bg-white p-6 border rounded-lg shadow-sm">
          <h3 className="text-xl font-semibold mb-4 border-b pb-2">Cast Your Vote</h3>
          {hasVoted ? (
            <p className="text-gray-600">You have already submitted your preferences for this event. You can update them by submitting again.</p>
          ) : (
             <p className="text-gray-600 mb-4">Select your top 3 preferences among the participants.</p>
          )}

          <form onSubmit={handleVote} className="space-y-4 mt-4">
            {[1, 2, 3].map(rank => (
              <div key={rank}>
                <label className="block text-gray-700 mb-1">Preference {rank}</label>
                <select
                  value={rank === 1 ? pref1 : rank === 2 ? pref2 : pref3}
                  onChange={e => rank === 1 ? setPref1(e.target.value) : rank === 2 ? setPref2(e.target.value) : setPref3(e.target.value)}
                  className="w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  required
                >
                  <option value="">Select a participant...</option>
                  {participants.map(p => (
                    <option key={p.id} value={p.id}>{p.username}</option>
                  ))}
                </select>
              </div>
            ))}
            <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition">
              {hasVoted ? "Update Vote" : "Submit Vote"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default EventDetails;
