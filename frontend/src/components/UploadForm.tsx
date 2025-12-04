import React, { useState } from 'react'
import axios from 'axios'

export default function UploadForm(){
  const [file, setFile] = useState<File | null>(null)
  const [msg, setMsg] = useState('')

  async function handleSubmit(e: React.FormEvent){
    e.preventDefault()
    if(!file) return setMsg('Choose a file')

    const fd = new FormData()
    fd.append('file', file)

    try{
      const r = await axios.post('/api/upload', fd, { headers: {'Content-Type': 'multipart/form-data'} })
      setMsg('Uploaded, job id: ' + r.data.id)
    }catch(err:any){
      setMsg('Upload error: ' + (err?.message || err))
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
      <input type="file" onChange={e => setFile(e.target.files?.[0] ?? null)} />
      <button type="submit">Upload & Queue</button>
      <div style={{ marginLeft: 10 }}>{msg}</div>
    </form>
  )
}
