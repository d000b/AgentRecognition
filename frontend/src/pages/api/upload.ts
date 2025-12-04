import type { NextApiRequest, NextApiResponse } from 'next'
import formidable from 'formidable'
import fs from 'fs'

export const config = { api: { bodyParser: false } }

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const form = new formidable.IncomingForm()
  form.parse(req, function(err, fields, files){
    if(err) return res.status(500).json({ error: err })

    // Save tmp file
    const f = files.file as formidable.File
    const data = fs.readFileSync(f.filepath)

    // Proxy to backend
    const fetch = require('node-fetch')
    const FormData = require('form-data')
    const fd = new FormData()
    fd.append('file', data, f.originalFilename)

    fetch(process.env.BACKEND_URL + '/documents', { method: 'POST', body: fd })
      .then(r => r.json())
      .then(j => res.status(200).json(j))
      .catch(e => res.status(500).json({ error: e.message }))
  })
}