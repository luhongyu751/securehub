import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { Typography, Box, Button, List, ListItem, ListItemText, CircularProgress, TextField, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import { useNavigate } from 'react-router-dom'

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api'

export default function DocList(){
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(false)
  const [openUpload, setOpenUpload] = useState(false)
  const [file, setFile] = useState(null)
  const [q, setQ] = useState('')
  const [token, setToken] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [otp, setOtp] = useState('')

  useEffect(()=>{ fetchDocs() }, [])

  useEffect(()=>{
    if(token){
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
  }, [token])

  async function doLogin(){
    if(!username || !password) { alert('请输入用户名和密码'); return }
    let pwd = password
    if(otp) pwd = `${password}:${otp}`
    try{
      const params = new URLSearchParams()
      params.append('username', username)
      params.append('password', pwd)
      const res = await axios.post(`${API_BASE}/token`, params)
      if(res.data && res.data.access_token){
        setToken(res.data.access_token)
        alert('登录成功')
      }
    }catch(e){
      console.error(e)
      alert('登录失败')
    }
  }

  function fetchDocs(){
    setLoading(true)
    axios.get(`${API_BASE}/documents`).then(r=>{
      setDocs(r.data.items || r.data)
    }).catch(e=>{ console.error(e) }).finally(()=>setLoading(false))
  }

  function handleOpenUpload(){ setOpenUpload(true) }
  function handleCloseUpload(){ setOpenUpload(false); setFile(null) }

  function doUpload(){
    if(!file) return
    const fd = new FormData()
    fd.append('file', file)
    axios.post(`${API_BASE}/documents/upload`, fd, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r=>{
      handleCloseUpload()
      fetchDocs()
    }).catch(e=>{ console.error(e); alert('Upload failed') })
  }

  return (
    <Box mt={4}>
      <Typography variant="h4" gutterBottom>文档管理</Typography>
      <Box mb={2} display="flex" gap={2}>
        <TextField label="搜索" value={q} onChange={(e)=>setQ(e.target.value)} />
        <Button variant="contained" onClick={fetchDocs}>刷新</Button>
        <Button variant="outlined" onClick={handleOpenUpload}>上传文档</Button>
        <Button variant="text" onClick={()=> navigate('/logs')}>下载记录</Button>
      </Box>

      <Box mb={2} display="flex" gap={2} alignItems="center">
        <TextField label="用户名" value={username} onChange={(e)=>setUsername(e.target.value)} />
        <TextField label="密码" type="password" value={password} onChange={(e)=>setPassword(e.target.value)} />
        <TextField label="2FA Code (可选)" value={otp} onChange={(e)=>setOtp(e.target.value)} />
        <Button variant="contained" onClick={doLogin}>登录</Button>
      </Box>

      <Box mb={2} display="flex" gap={2} alignItems="center">
        <TextField label="或粘贴 JWT Token" value={token} onChange={(e)=>setToken(e.target.value)} fullWidth />
      </Box>

      {loading ? <CircularProgress /> : (
        <List>
          {(docs || []).map(d=> (
            <ListItem key={d.id} divider>
              <ListItemText primary={d.filename} secondary={d.watermark_enabled ? '带水印' : '不带水印'} />
              <Button component="a" href={`${API_BASE}/documents/${d.id}/download`} target="_blank">下载</Button>
            </ListItem>
          ))}
        </List>
      )}

      <Dialog open={openUpload} onClose={handleCloseUpload}>
        <DialogTitle>上传 PDF</DialogTitle>
        <DialogContent>
          <input type="file" accept="application/pdf" onChange={(e)=>setFile(e.target.files[0])} />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseUpload}>取消</Button>
          <Button onClick={doUpload} variant="contained">上传</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
