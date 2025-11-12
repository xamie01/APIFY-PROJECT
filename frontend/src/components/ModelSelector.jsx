import React from 'react'

export default function ModelSelector({ models = [], value, onChange }){
  return (
    <div className="model-selector">
      <label htmlFor="model">Select Model</label>
      <select id="model" value={value || ''} onChange={e => onChange(e.target.value)}>
        {models.map(m => (
          <option key={m} value={m}>{m}</option>
        ))}
      </select>
    </div>
  )
}
