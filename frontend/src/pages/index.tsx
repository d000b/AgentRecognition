import React, { useState, useEffect } from 'react'
import UploadForm from '../components/UploadForm'
import JobsPanel from '../components/JobsPanel'


export default function Home() {
    return (
        <div style={{ padding: 20, fontFamily: 'Inter, Arial' }}>
        <h1>OCR Service</h1>
        <p>Upload files (PDF, PNG, JPG) or an archive for batch processing.</p>

        <UploadForm />
        <hr style={{ margin: '20px 0' }} />
        <JobsPanel />
        </div>
    )
}
