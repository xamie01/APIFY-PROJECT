import React, { useState } from 'react'
import axios from 'axios'

export default function Sandbox(){
  const [name, setName] = useState('my-sandbox')
  const [command, setCommand] = useState('python -c "print(\'hello\')"')
  const [output, setOutput] = useState(null)

  async function create(){
    try{
      const res = await axios.post('/api/sandbox/create', { name })
      setOutput(`✓ Created sandbox: ${res.data.sandbox_name}`)
      alert(`Created sandbox: ${res.data.sandbox_name}`)
    }catch(e){
      const msg = e.response?.data?.error || e.message || 'Create failed'
      setOutput(`✗ Error: ${msg}`)
      alert(`Create failed: ${msg}`)
      console.error(e)
    }
  }

  async function run(){
    try{
      const res = await axios.post('/api/sandbox/execute', { sandbox_name: name, command })
      setOutput(JSON.stringify(res.data.result, null, 2))
    }catch(e){
      const msg = e.response?.data?.error || e.message || 'Execution failed'
      setOutput(`✗ Error: ${msg}`)
      console.error(e)
    }
  }

  return (
    <div className="sandbox">
      <label>Sandbox Name</label>
      <input value={name} onChange={e=>setName(e.target.value)} />
      <label>Command</label>
      <input value={command} onChange={e=>setCommand(e.target.value)} />
      <div className="controls">
        <button className="btn" onClick={create}>Create</button>
        <button className="btn" onClick={run}>Run</button>
      </div>
      {output && (
        <pre className="code">{output}</pre>
      )}
    </div>
  )
}
