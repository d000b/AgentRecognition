import type { NextApiRequest, NextApiResponse } from 'next'
import formidable from 'formidable'
import { createReadStream, unlinkSync } from 'fs'
// import { FormData } from 'undici'

export const config = { api: { bodyParser: false } }

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const form = new formidable.IncomingForm()

  form.parse(req, async function (err, fields, files) {
    if (err) return res.status(500).json({ error: err })

    try {
      const f = files.file as formidable.File

      const fd = new FormData()
      const stream = createReadStream(f.filepath)

      fd.append('file', stream, {
        filename: f.originalFilename || f.newFilename,
        contentType: f.mimetype ?? 'application/octet-stream'
      })

      const response = await fetch(process.env.BACKEND_URL + '/documents', {
        method: 'POST',
        body: fd
      })

      unlinkSync(f.filepath)

      const result = await response.json()
      res.status(200).json(result)
    } catch (e: any) {
      res.status(500).json({ error: e.message })
    }
  })
}
