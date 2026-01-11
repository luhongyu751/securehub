import React, { useEffect, useState } from 'react'
import { Box, Typography, Table, TableBody, TableCell, TableHead, TableRow, Button } from '@mui/material'
import api from '../utils/api'

export default function UserDocs({ token }){
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(()=>{ if(token) fetchDocs() }, [token])

  async function fetchDocs(){
    setLoading(true)
    try{
      const resp = await api.get('/api/documents')
      setItems(resp.data.items || [])
    }catch(err){ console.error(err) }
    finally{ setLoading(false) }
  }

  function download(doc){
    // trigger browser download via fetch to preserve streaming
    fetch(`/api/documents/${doc.id}/download`, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
      .then(resp=>{
        if(!resp.ok) throw new Error(`Download failed: ${resp.status}`)
        return resp.blob()
      })
      .then(blob=>{
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = doc.filename
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
      })
      .catch(err=>{ alert(err.message) })
  }

  return (
    <Box p={2}>
      <Typography variant="h6">可下载文档</Typography>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>文件名</TableCell>
            <TableCell>水印启用</TableCell>
            <TableCell>操作</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map(it=> (
            <TableRow key={it.id}>
              <TableCell>{it.filename}</TableCell>
              <TableCell>{it.watermark_enabled ? '是' : '否'}</TableCell>
              <TableCell><Button onClick={()=>download(it)}>下载</Button></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  )
}
