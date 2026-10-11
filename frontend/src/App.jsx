import { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [backendStatus, setBackendStatus] = useState('Checking backend...');
  const [books] = useState([
    { id: 1, title: 'The Pragmatic Programmer', author: 'Andrew Hunt & David Thomas', price: 40.00 },
    { id: 2, title: 'Clean Code', author: 'Robert C. Martin', price: 35.50 },
    { id: 3, title: 'Fluent Python', author: 'Luciano Ramalho', price: 45.00 }
  ]);

  // Test connection to Flask backend health route
  useEffect(() => {
    fetch('http://localhost:5000/api/health')
      .then(res => res.json())
      .then(data => setBackendStatus(data.message))
      .catch(() => setBackendStatus('Backend is offline or unreachable'));
  }, []);

  return (
    <div className="app-container" style={{ fontFamily: 'Arial, sans-serif', margin: '0', padding: '20px', backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
      {/* Header */}
      <header style={{ backgroundColor: '#2c3e50', color: 'white', padding: '20px', borderRadius: '8px', textAlign: 'center' }}>
        <h1>📚 SmartBase Online Bookstore</h1>
        <p>Your hub for developer and tech books</p>
        <div style={{ marginTop: '10px', fontSize: '14px', background: '#34495e', padding: '8px', borderRadius: '4px', display: 'inline-block' }}>
          <strong>Backend Status:</strong> {backendStatus}
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: '900px', margin: '30px auto' }}>
        <h2>Featured Books</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginTop: '15px' }}>
          {books.map(book => (
            <div key={book.id} style={{ background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
              <h3 style={{ margin: '0 0 10px 0', color: '#2c3e50' }}>{book.title}</h3>
              <p style={{ color: '#7f8c8d', margin: '0 0 10px 0' }}>By {book.author}</p>
              <p style={{ fontWeight: 'bold', color: '#27ae60', fontSize: '18px' }}>${book.price.toFixed(2)}</p>
              <button style={{ backgroundColor: '#3498db', color: 'white', border: 'none', padding: '10px 15px', borderRadius: '4px', cursor: 'pointer', width: '100%', fontWeight: 'bold' }}>
                Add to Cart
              </button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

export default App;