import type { NextApiRequest, NextApiResponse } from 'next'
import formidable from 'formidable'
import { createReadStream, unlinkSync } from 'fs'

export const config = { api: { bodyParser: false } }

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const form = new formidable.IncomingForm()
  
  form.parse(req, async function(err, fields, files) {
    if (err) return res.status(500).json({ error: err })

    try {
      const f = files.file as formidable.File
      
      const fd = new FormData()
      // Create a Blob from the file stream
      const fileStream = createReadStream(f.filepath)
      const chunks: Buffer[] = []
      
      for await (const chunk of fileStream) {
        chunks.push(chunk)
      }
      
      const blob = new Blob(chunks)
      fd.append('file', blob, f.originalFilename || f.newFilename)
      
      // Clean up temp file
      unlinkSync(f.filepath)
      
      const response = await fetch(process.env.BACKEND_URL + '/documents', {
        method: 'POST',
        body: fd
      })
      
      const result = await response.json()
      res.status(200).json(result)
    } catch (e: any) {
      res.status(500).json({ error: e.message })
    }
  })
}