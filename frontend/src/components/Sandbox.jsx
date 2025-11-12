import React, { useState } from 'react'
import axios from 'axios'

export default function Sandbox(){
  const [name, setName] = useState('my-sandbox')
  const [command, setCommand] = useState('python -c "print(\'hello\')"')
  const [output, setOutput] = useState(null)

  async function create(){
    try{
      const res = await axios.post('/api/sandbox/create', { name })
      alert(`Created sandbox: ${res.data.sandbox_name}`)
    }catch(e){
      alert('Create failed')
    }
  }

  async function run(){
    try{
      const res = await axios.post('/api/sandbox/execute', { sandbox_name: name, command })
      setOutput(JSON.stringify(res.data.result, null, 2))
    }catch(e){
      setOutput('Execution failed')
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
