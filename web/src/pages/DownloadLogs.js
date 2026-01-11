import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { Typography, Box, Table, TableBody, TableCell, TableHead, TableRow, CircularProgress, Button, TextField, Paper } from '@mui/material'
import { useNavigate } from 'react-router-dom'

function toCSV(rows){
  if(!rows || rows.length===0) return ''
  const keys = Object.keys(rows[0])
  const escape = (v) => '"' + (v === null || v === undefined ? '' : String(v).replace(/"/g, '""')) + '"'
  const header = keys.join(',')
  const lines = rows.map(r => keys.map(k => escape(r[k])).join(','))
  return [header].concat(lines).join('\n')
}

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api'

export default function DownloadLogs(){
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [username, setUsername] = useState('')
  const [startTs, setStartTs] = useState('')
  const [endTs, setEndTs] = useState('')
  const [exporting, setExporting] = useState(false)
  const [progress, setProgress] = useState(0)

  useEffect(()=>{ fetchLogs() }, [])
  const navigate = useNavigate()

  function fetchLogs(){
    setLoading(true)
    const params = {}
    if(username) params.username = username
    if(startTs) params.start_ts = startTs
    if(endTs) params.end_ts = endTs
    axios.get(`${API_BASE}/logs`, { params }).then(r=>{
      setLogs(r.data.items || [])
    }).catch(e=>{ console.error(e); alert('加载失败，确认你使用管理员 token') }).finally(()=>setLoading(false))
  }

  function exportCSV(){
    // server-side export with progress and record history
    setExporting(true)
    setProgress(0)
    const params = new URLSearchParams()
    if(username) params.append('username', username)
    if(startTs) params.append('start_ts', startTs)
    if(endTs) params.append('end_ts', endTs)
    const url = `${API_BASE}/logs/export?` + params.toString()

    // add history entry
    const id = String(Date.now())
    const histItem = { id, time: new Date().toISOString(), filters: { username, startTs, endTs }, status: 'in-progress' }
    try{ const raw = localStorage.getItem('securehub_export_history'); const arr = raw ? JSON.parse(raw) : []; arr.unshift(histItem); localStorage.setItem('securehub_export_history', JSON.stringify(arr)) }catch(e){}

    fetch(url, { headers: axios.defaults.headers.common }).then(async res => {
      if(!res.ok) throw new Error('导出失败')
      const contentLength = res.headers.get('content-length')
      const total = contentLength ? parseInt(contentLength, 10) : null
      const reader = res.body.getReader()
      const chunks = []
      let received = 0
      while(true){
        const { done, value } = await reader.read()
        if(done) break
        chunks.push(value)
        received += value.length
        if(total) setProgress(Math.round((received/total)*100))
      }
      const blob = new Blob(chunks, { type: 'text/csv' })
      const filename = `download_logs_${new Date().toISOString().slice(0,19).replace(/[:T]/g,'_')}.csv`
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = filename
      a.click()

      // update history item as completed
      try{
        const raw = localStorage.getItem('securehub_export_history');
        const arr = raw ? JSON.parse(raw) : [];
        const idx = arr.findIndex(x=>x.id===id);
        if(idx>=0){ arr[idx].status = 'completed'; arr[idx].filename = filename; arr[idx].downloadUrl = a.href; localStorage.setItem('securehub_export_history', JSON.stringify(arr)); }
      }catch(e){}

      setTimeout(()=>{ URL.revokeObjectURL(a.href); setExporting(false); setProgress(0) }, 5000)
    }).catch(e=>{
      console.error(e);
      alert('导出失败');
      setExporting(false);
      setProgress(0);
      try{
        const raw = localStorage.getItem('securehub_export_history');
        const arr = raw ? JSON.parse(raw) : [];
        const idx = arr.findIndex(x=>x.id===id);
        if(idx>=0){ arr[idx].status = 'failed'; localStorage.setItem('securehub_export_history', JSON.stringify(arr)); }
      }catch(err){}
    })
  }

  return (
    <Box mt={4}>
      <Typography variant="h4" gutterBottom>下载记录</Typography>

      <Paper sx={{ p:2, mb:2 }}>
        <Box display="flex" gap={2} alignItems="center" mb={1}>
          <TextField label="用户名（模糊）" value={username} onChange={(e)=>setUsername(e.target.value)} />
          <TextField label="开始时间 (ISO)" placeholder="2026-01-01T00:00:00" value={startTs} onChange={(e)=>setStartTs(e.target.value)} />
          <TextField label="结束时间 (ISO)" placeholder="2026-01-31T23:59:59" value={endTs} onChange={(e)=>setEndTs(e.target.value)} />
          <Button variant="contained" onClick={fetchLogs}>筛选 / 刷新</Button>
          <Button variant="outlined" onClick={exportCSV}>导出 CSV</Button>
          <Button variant="text" onClick={()=>navigate('/exports')}>导出历史</Button>
        </Box>
        <Box>
          <Typography variant="caption">提示：时间采用 ISO 格式，如 2026-01-01T00:00:00（可留空）</Typography>
        </Box>
      </Paper>

      {exporting && (
        <Box mb={2}>
          <Typography>导出中... {progress}%</Typography>
          <progress value={progress} max={100} style={{ width: '100%' }} />
        </Box>
      )}

      {loading ? <CircularProgress /> : (
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>时间</TableCell>
              <TableCell>用户名</TableCell>
              <TableCell>文档</TableCell>
              <TableCell>客户端 IP</TableCell>
              <TableCell>动作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs.map(l => (
              <TableRow key={l.id}>
                <TableCell>{l.timestamp}</TableCell>
                <TableCell>{l.username}</TableCell>
                <TableCell>{l.filename}</TableCell>
                <TableCell>{l.client_ip}</TableCell>
                <TableCell>
                  <Button component="a" href={`${API_BASE}/documents/${l.document_id}/download`} target="_blank">下载</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Box>
  )
}
