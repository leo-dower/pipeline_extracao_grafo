import { useState, useEffect } from 'react';
import './App.css'; // Assuming App.css for basic styling

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState({ tribunal: '', classe: '', uf: '' });
  const [aggregations, setAggregations] = useState({ tribunals: [], classes: [], uf: [] });
  const [groqText, setGroqText] = useState('');
  const [groqAnalysis, setGroqAnalysis] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const API_BASE_URL = '/api'; // Use proxy for backend calls

  // Fetch aggregations on component mount
  useEffect(() => {
    const fetchAggregations = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/aggregations`, {
          method: 'POST', // Aggregations endpoint is POST
          headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setAggregations(data);
      } catch (error) {
        console.error("Error fetching aggregations:", error);
        setError("Failed to load filters.");
      }
    };
    fetchAggregations();
  }, []);

  const fetchSearchResults = async (page = 1) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query_string: searchQuery,
          tribunal: filters.tribunal,
          classe: filters.classe,
          uf: filters.uf,
          page: page,
          size: 10, // Display 10 results per page
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSearchResults(data.hits);
      setTotalResults(data.total);
      setCurrentPage(page);
    } catch (error) {
      console.error("Error fetching search results:", error);
      setError("Failed to fetch search results.");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchSearchResults(1); // Start new search from page 1
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prevFilters => ({ ...prevFilters, [name]: value }));
  };

  const handleGroqAnalysis = async () => {
    setLoading(true);
    setError(null);
    setGroqAnalysis('');
    try {
      const response = await fetch(`${API_BASE_URL}/ai-analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: groqText }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setGroqAnalysis(data.analysis);
    } catch (error) {
      console.error("Error during Groq analysis:", error);
      setError("Failed to get AI analysis. Check Groq API key and text length.");
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(totalResults / 10);

  return (
    <div className="App">
      <header className="App-header">
        <h1>CNJ DataJud Search & AI Analysis</h1>
      </header>

      <section className="search-section">
        <h2>Search Processes</h2>
        <div className="search-controls">
          <input
            type="text"
            placeholder="Search by process number, name, etc."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => { if (e.key === 'Enter') handleSearch(); }}
          />
          <button onClick={handleSearch} disabled={loading}>Search</button>
        </div>

        <div className="filters">
          <select name="tribunal" value={filters.tribunal} onChange={handleFilterChange}>
            <option value="">All Tribunals</option>
            {aggregations.tribunals.map(agg => (
              <option key={agg.key} value={agg.key}>{agg.key} ({agg.doc_count})</option>
            ))}
          </select>
          <select name="classe" value={filters.classe} onChange={handleFilterChange}>
            <option value="">All Classes</option>
            {aggregations.classes.map(agg => (
              <option key={agg.key} value={agg.key}>{agg.key} ({agg.doc_count})</option>
            ))}
          </select>
          <select name="uf" value={filters.uf} onChange={handleFilterChange}>
            <option key="" value="">All UFs</option>
            {aggregations.uf.map(agg => (
              <option key={agg.key} value={agg.key}>{agg.key} ({agg.doc_count})</option>
            ))}
          </select>
          <button onClick={handleSearch} disabled={loading}>Apply Filters</button>
        </div>

        {loading && <p>Loading...</p>}
        {error && <p className="error-message">{error}</p>}

        <div className="search-results">
          <h3>Results ({totalResults})</h3>
          {searchResults.length === 0 && !loading && !error && <p>No results found. Try a different query or filters.</p>}
          {searchResults.map((process) => (
            <div key={process.numeroProcesso} className="process-card">
              <h4>{process.numeroProcesso}</h4>
              <p><strong>Tribunal:</strong> {process.orgaoJulgador?.nome || 'N/A'}</p>
              <p><strong>Classe:</strong> {process.classe?.nome || 'N/A'}</p>
              <p><strong>UF:</strong> {process.uf || 'N/A'}</p>
              <p><strong>Data Ajuizamento:</strong> {process.dataAjuizamento || 'N/A'}</p>
              {/* Add more details as needed */}
            </div>
          ))}
        </div>

        {totalPages > 1 && (
          <div className="pagination">
            <button onClick={() => fetchSearchResults(currentPage - 1)} disabled={currentPage === 1 || loading}>Previous</button>
            <span>Page {currentPage} of {totalPages}</span>
            <button onClick={() => fetchSearchResults(currentPage + 1)} disabled={currentPage === totalPages || loading}>Next</button>
          </div>
        )}
      </section>

      <section className="ai-analysis-section">
        <h2>AI Analysis (Groq)</h2>
        <textarea
          placeholder="Enter text for AI analysis (e.g., a legal excerpt, process description)..."
          value={groqText}
          onChange={(e) => setGroqText(e.target.value)}
          rows="10"
          cols="50"
        ></textarea>
        <button onClick={handleGroqAnalysis} disabled={loading || !groqText.trim()}>Analyze with Groq</button>
        {loading && groqAnalysis === '' && <p>Analyzing...</p>}
        {groqAnalysis && (
          <div className="ai-result">
            <h3>AI Insights:</h3>
            <p>{groqAnalysis}</p>
          </div>
        )}
      </section>
    </div>
  );
}

export default App;