import React, { useEffect, useState } from 'react'
import axios from 'axios'
import Header from './components/Header'
import Footer from './components/Footer'
import ModelSelector from './components/ModelSelector'
import AIQuery from './components/AIQuery'
import Sandbox from './components/Sandbox'
import SafetyTestPanel from './components/SafetyTestPanel'

export default function App() {
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState(null)

  useEffect(() => {
    fetchModels()
  }, [])

  async function fetchModels() {
    try {
      const res = await axios.get('/api/models')
      if (res.data && res.data.models) {
        setModels(res.data.models)
        setSelectedModel(res.data.models[0] || null)
      }
    } catch (err) {
      console.error('Failed to fetch models', err)
    }
  }

  return (
    <div className="app-root">
      <Header />
      <main className="container">
        {/* Safety Test Panel - Full Width */}
        <div style={{ gridColumn: '1 / -1', marginBottom: '20px' }}>
          <SafetyTestPanel />
        </div>

        <section className="left">
          <div className="card">
            <h2>AI Model Testing</h2>
            <ModelSelector models={models} value={selectedModel} onChange={setSelectedModel} />
            <AIQuery model={selectedModel} />
          </div>
        </section>

        <aside className="right">
          <div className="card">
            <h3>Sandbox</h3>
            <Sandbox />
          </div>

          <div className="card">
            <h3>Health</h3>
            <button className="btn" onClick={async () => {
              try {
                const res = await axios.get('/api/health')
                alert(JSON.stringify(res.data, null, 2))
              } catch (e) {
                alert('Health check failed')
              }
            }}>Check Health</button>
          </div>
        </aside>
      </main>
      <Footer />
    </div>
  )
}
