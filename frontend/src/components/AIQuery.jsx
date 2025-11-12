import React, { useState } from 'react'
import axios from 'axios'

export default function AIQuery({ model }){
  const [prompt, setPrompt] = useState('')
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)

  async function submit(){
    if(!model){ alert('Select a model first'); return }
    setLoading(true)
    try{
      const res = await axios.post('/api/query', { model, prompt })
      setResponse(res.data)
    }catch(e){
      console.error(e)
      setResponse({ success: false, error: 'Request failed' })
    }finally{
      setLoading(false)
    }
  }

  return (
    <div className="ai-query">
      <label>Prompt</label>
      <textarea value={prompt} onChange={e=>setPrompt(e.target.value)} rows={6} />
      <div className="controls">
        <button className="btn" onClick={submit} disabled={loading}>{loading? 'Running...':'Submit Query'}</button>
      </div>

      {response && (
        <div className="response">
          <h4>Response</h4>
          {response.success ? (
            <pre className="code">{typeof response.response === 'string' ? response.response : JSON.stringify(response.response, null, 2)}</pre>
          ) : (
            <div className="error">{response.error || 'Unknown error'}</div>
          )}
        </div>
      )}
    </div>
  )
}
