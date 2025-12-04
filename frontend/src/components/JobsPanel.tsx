import React, { useEffect, useState } from 'react'
import axios from 'axios'

type Job = { id:number, filename:string, status:string }

export default function JobsPanel(){
  const [jobs, setJobs] = useState<Job[]>([])

  async function load(){
    try{
      const r = await axios.get('/api/jobs')
      setJobs(r.data)
    }catch(e){ console.error(e) }
  }

  useEffect(()=>{ load(); const t = setInterval(load, 4000); return ()=>clearInterval(t) }, [])

  return (
    <div>
      <h3>Jobs</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead><tr><th>ID</th><th>Filename</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>
          {jobs.map(j => (
            <tr key={j.id}>
              <td>{j.id}</td>
              <td>{j.filename}</td>
              <td>{j.status}</td>
              <td>
                {j.status === 'done' && <a href={`/api/result/${j.id}`}>Download</a>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
