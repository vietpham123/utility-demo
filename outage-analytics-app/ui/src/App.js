import React, { useEffect, useState } from 'react';

function App() {
  const [outages, setOutages] = useState([]);
  const [usage, setUsage] = useState([]);

  useEffect(() => {
    fetch('http://localhost:3001/api/outages')
      .then(res => res.json())
      .then(setOutages);
    fetch('http://localhost:3001/api/usage')
      .then(res => res.json())
      .then(setUsage);
  }, []);

  return (
    <div>
      <h1>Outage List</h1>
      <table border="1">
        <thead>
          <tr><th>ID</th><th>Location</th><th>Status</th><th>Affected Customers</th></tr>
        </thead>
        <tbody>
          {outages.map(o => (
            <tr key={o.id}>
              <td>{o.id}</td><td>{o.location}</td><td>{o.status}</td><td>{o.affectedCustomers}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h1>Energy Usage</h1>
      <table border="1">
        <thead>
          <tr><th>ID</th><th>Customer ID</th><th>Timestamp</th><th>Usage (kWh)</th></tr>
        </thead>
        <tbody>
          {usage.map(u => (
            <tr key={u.id}>
              <td>{u.id}</td><td>{u.customerId}</td><td>{u.timestamp}</td><td>{u.usageKWh}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
