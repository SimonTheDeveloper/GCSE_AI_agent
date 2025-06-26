import React, { useEffect, useState } from "react";
import logo from './logo.svg';
import './App.css';

function App() {
  const [message, setMessage] = useState("");
  const [input, setInput] = useState("");

  useEffect(() => {
    fetch("/api/message")
      .then(res => res.json())
      .then(data => setMessage(data.message));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    await fetch("/api/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: input }),
    });
    setMessage(input);
    setInput("");
  };

  return (
    <div className="App">
      <h1>Message from DB: {message}</h1>
      <form onSubmit={handleSubmit}>
        <input value={input} onChange={e => setInput(e.target.value)} />
        <button type="submit">Save Message</button>
      </form>
    </div>
  );
}

export default App;
