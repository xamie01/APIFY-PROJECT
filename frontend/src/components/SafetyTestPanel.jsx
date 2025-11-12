import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './SafetyTestPanel.css';

export default function SafetyTestPanel() {
  const [models, setModels] = useState([]);
  const [categories, setCategories] = useState({});
  const [selectedModels, setSelectedModels] = useState(['openrouter-mistral-7b']);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSubcategory, setSelectedSubcategory] = useState('');
  const [limit, setLimit] = useState(10);
  const [testing, setTesting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStatus, setCurrentStatus] = useState('');
  const [results, setResults] = useState(null);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');
  const [showResults, setShowResults] = useState(false);

  // Load initial data
  useEffect(() => {
    loadModels();
    loadCategories();
    loadStatistics();
  }, []);

  const loadModels = async () => {
    try {
      const response = await axios.get('/api/tests/models');
      if (response.data.status === 'success') {
        setModels(response.data.models);
      }
    } catch (err) {
      console.error('Error loading models:', err);
      setError('Failed to load models');
    }
  };

  const loadCategories = async () => {
    try {
      const response = await axios.get('/api/tests/categories');
      if (response.data.status === 'success') {
        setCategories(response.data.categories);
      }
    } catch (err) {
      console.error('Error loading categories:', err);
      setError('Failed to load categories');
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await axios.get('/api/tests/statistics');
      if (response.data.status === 'success') {
        setStats(response.data.statistics);
      }
    } catch (err) {
      console.error('Error loading statistics:', err);
    }
  };

  const handleRunTest = async () => {
    if (selectedModels.length === 0) {
      setError('Please select at least one model');
      return;
    }

    setTesting(true);
    setProgress(0);
    setError('');
    setCurrentStatus('Starting tests...');

    try {
      const response = await axios.post('/api/tests/run', {
        models: selectedModels,
        category: selectedCategory || null,
        subcategory: selectedSubcategory || null,
        limit: parseInt(limit)
      });

      if (response.data.status === 'success') {
        setResults(response.data);
        setProgress(100);
        setCurrentStatus('Tests completed!');
        setShowResults(true);

        // Reload statistics
        setTimeout(() => {
          loadStatistics();
        }, 1000);
      } else {
        setError(response.data.message || 'Test failed');
        setCurrentStatus('Test failed');
      }
    } catch (err) {
      console.error('Error running tests:', err);
      setError(err.response?.data?.message || err.message || 'Error running tests');
      setCurrentStatus('Error occurred');
    } finally {
      setTesting(false);
    }
  };

  const handleModelToggle = (model) => {
    setSelectedModels(prev =>
      prev.includes(model)
        ? prev.filter(m => m !== model)
        : [...prev, model]
    );
  };

  const handleCategoryChange = (category) => {
    setSelectedCategory(category);
    setSelectedSubcategory('');
  };

  const getSubcategories = () => {
    if (!selectedCategory || !categories[selectedCategory]) {
      return {};
    }
    return categories[selectedCategory].subcategories || {};
  };

  const getRefusalRate = (passed, failed) => {
    const total = passed + failed;
    return total > 0 ? ((passed / total) * 100).toFixed(1) : 0;
  };

  return (
    <div className="safety-test-panel">
      <div className="panel-header">
        <div className="header-content">
          <h1>🧪 AI Safety Test Suite</h1>
          <p className="subtitle">Test AI models for dangerous capabilities, alignment violations, and instrumental convergence</p>
        </div>
      </div>

      {error && (
        <div className="error-alert">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {/* Statistics Dashboard */}
      {stats && (
        <div className="stats-dashboard">
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <div className="stat-label">Tests Run</div>
              <div className="stat-value">{stats.total_tests_run}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🎯</div>
            <div className="stat-content">
              <div className="stat-label">Prompts Tested</div>
              <div className="stat-value">{stats.total_prompts_tested}</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🛡️</div>
            <div className="stat-content">
              <div className="stat-label">Refusal Rate</div>
              <div className="stat-value">{(stats.overall_refusal_rate * 100).toFixed(1)}%</div>
            </div>
          </div>
          {stats.latest_test && (
            <div className="stat-card">
              <div className="stat-icon">⏱️</div>
              <div className="stat-content">
                <div className="stat-label">Last Test</div>
                <div className="stat-value">{new Date(stats.latest_test.timestamp).toLocaleDateString()}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Test Configuration */}
      <div className="test-configuration">
        <h2>Configure Test</h2>

        {/* Model Selection */}
        <div className="config-section">
          <label className="section-label">
            <span className="label-icon">🤖</span>
            Select Models ({selectedModels.length} selected)
          </label>
          <div className="model-grid">
            {models.map(model => (
              <button
                key={model}
                className={`model-button ${selectedModels.includes(model) ? 'selected' : ''}`}
                onClick={() => handleModelToggle(model)}
              >
                <input
                  type="checkbox"
                  checked={selectedModels.includes(model)}
                  onChange={() => {}}
                  style={{ display: 'none' }}
                />
                <span className="model-name">{model.replace('openrouter-', '')}</span>
                {selectedModels.includes(model) && <span className="checkmark">✓</span>}
              </button>
            ))}
          </div>
        </div>

        {/* Category Selection */}
        <div className="config-section">
          <label className="section-label">
            <span className="label-icon">📂</span>
            Select Category
          </label>
          <select
            value={selectedCategory}
            onChange={(e) => handleCategoryChange(e.target.value)}
            className="config-select"
          >
            <option value="">All Categories</option>
            {Object.entries(categories).map(([cat, data]) => (
              <option key={cat} value={cat}>
                {cat} ({data.total} prompts)
              </option>
            ))}
          </select>
        </div>

        {/* Subcategory Selection */}
        {selectedCategory && (
          <div className="config-section">
            <label className="section-label">
              <span className="label-icon">📌</span>
              Select Subcategory
            </label>
            <select
              value={selectedSubcategory}
              onChange={(e) => setSelectedSubcategory(e.target.value)}
              className="config-select"
            >
              <option value="">All Subcategories</option>
              {Object.entries(getSubcategories()).map(([subcat, data]) => (
                <option key={subcat} value={subcat}>
                  {subcat} ({data.count} prompts)
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Limit Selection */}
        <div className="config-section">
          <label className="section-label">
            <span className="label-icon">🔢</span>
            Limit Prompts (1-180)
          </label>
          <input
            type="number"
            min="1"
            max="180"
            value={limit}
            onChange={(e) => setLimit(Math.min(180, Math.max(1, parseInt(e.target.value) || 1)))}
            className="config-input"
            disabled={testing}
          />
        </div>

        {/* Run Button and Progress */}
        <div className="run-section">
          <button
            onClick={handleRunTest}
            disabled={testing || selectedModels.length === 0}
            className="btn-run-test"
          >
            {testing ? (
              <>
                <span className="spinner"></span>
                Running... {progress}%
              </>
            ) : (
              <>
                <span className="btn-icon">▶️</span>
                Run Safety Tests
              </>
            )}
          </button>
          {testing && <div className="progress-bar"><div className="progress-fill" style={{ width: `${progress}%` }}></div></div>}
          {currentStatus && <p className="status-text">{currentStatus}</p>}
        </div>
      </div>

      {/* Results Section */}
      {showResults && results && (
        <div className="results-section">
          <h2>Test Results</h2>

          {/* Results Summary */}
          <div className="results-summary">
            <div className="summary-card">
              <div className="summary-label">Total Prompts</div>
              <div className="summary-value">{results.summary?.tests_run || 0}</div>
            </div>
            <div className="summary-card">
              <div className="summary-label">Models Tested</div>
              <div className="summary-value">{results.summary?.models?.length || 0}</div>
            </div>
            <div className="summary-card success">
              <div className="summary-label">Passed (Safely Refused)</div>
              <div className="summary-value">
                {Object.values(results.results).reduce((sum, cat) => sum + (cat.passed || 0), 0)}
              </div>
            </div>
            <div className="summary-card danger">
              <div className="summary-label">Failed (Didn't Refuse)</div>
              <div className="summary-value">
                {Object.values(results.results).reduce((sum, cat) => sum + (cat.failed || 0), 0)}
              </div>
            </div>
          </div>

          {/* Detailed Results by Category */}
          <div className="results-details">
            <h3>Results by Category</h3>
            <div className="results-table">
              <table>
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Passed</th>
                    <th>Failed</th>
                    <th>Refusal Rate</th>
                    <th>Progress</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(results.results).map(([category, data]) => {
                    const rate = getRefusalRate(data.passed, data.failed);
                    return (
                      <tr key={category} className={parseFloat(rate) > 75 ? 'row-success' : 'row-warning'}>
                        <td className="category-name">{category}</td>
                        <td className="number passed">{data.passed}</td>
                        <td className="number failed">{data.failed}</td>
                        <td className="number rate">{rate}%</td>
                        <td className="progress-column">
                          <div className="mini-progress">
                            <div
                              className="mini-fill"
                              style={{ width: `${rate}%`, background: parseFloat(rate) > 75 ? '#4CAF50' : '#ff9800' }}
                            ></div>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Model Performance */}
          {results.test_log && results.test_log.length > 0 && (
            <div className="model-performance">
              <h3>Model Performance</h3>
              <div className="performance-grid">
                {Array.from(new Set(results.test_log.map(t => t.model))).map(model => {
                  const modelTests = results.test_log.filter(t => t.model === model);
                  const passed = modelTests.filter(t => t.passed).length;
                  const rate = ((passed / modelTests.length) * 100).toFixed(1);
                  return (
                    <div key={model} className="performance-card">
                      <div className="model-label">{model.replace('openrouter-', '')}</div>
                      <div className="model-rate">{rate}%</div>
                      <div className="model-tests">{modelTests.length} tests</div>
                      <div className="rate-bar">
                        <div className="rate-fill" style={{ width: `${rate}%` }}></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <button onClick={() => setShowResults(false)} className="btn-close-results">
            Close Results
          </button>
        </div>
      )}
    </div>
  );
}
