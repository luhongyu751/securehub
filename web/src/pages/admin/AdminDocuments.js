import React, { useEffect, useState } from 'react'
import { Box, Typography, Button, Table, TableBody, TableCell, TableHead, TableRow, Snackbar, Alert, CircularProgress, Dialog, DialogTitle, DialogActions } from '@mui/material'
import api from '../../utils/api'

export default function AdminDocuments(){
  const [docs, setDocs] = useState([])
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [snack, setSnack] = useState({ open: false, severity: 'info', message: '' })
  const [confirmDelete, setConfirmDelete] = useState({ open: false, id: null })

  async function load(){
    try{
      const r = await api.get('/api/documents')
      setDocs(r.data.items || [])
    }catch(e){ setSnack({ open:true, severity:'error', message: e.response?.data?.detail || e.message }) }
  }

  useEffect(()=>{ load() }, [])

  async function upload(){
    setSnack({ open:false, severity:'info', message:'' })
    if(!file){ setSnack({ open:true, severity:'error', message:'请选择文件' }); return }
    if(!file.name.toLowerCase().endsWith('.pdf')){ setSnack({ open:true, severity:'error', message:'仅支持 PDF' }); return }
    const fd = new FormData()
    fd.append('file', file)
    fd.append('watermark_enabled', true)
    setLoading(true)
    try{
      await api.post('/api/documents/upload', fd, { headers: {'Content-Type': 'multipart/form-data'} })
      setFile(null)
      setSnack({ open:true, severity:'success', message:'上传成功' })
      load()
    }catch(e){ setSnack({ open:true, severity:'error', message: e.response?.data?.detail || e.message }) }finally{ setLoading(false) }
  }

  async function doDelete(id){
    setConfirmDelete({ open:false, id: null })
    setLoading(true)
    try{
      await api.delete(`/api/documents/${id}`)
      setSnack({ open:true, severity:'success', message:'文档已删除' })
      load()
    }catch(e){ setSnack({ open:true, severity:'error', message: e.response?.data?.detail || e.message }) }finally{ setLoading(false) }
  }

  return (
    <Box mt={4}>
      <Typography variant="h5">文档管理</Typography>
      <Box mt={2} display="flex" gap={2} alignItems="center">
        <input type="file" accept="application/pdf" onChange={e=>setFile(e.target.files[0])} />
        <Button variant="contained" onClick={upload} disabled={loading}>{loading ? <CircularProgress size={16} /> : '上传'}</Button>
      </Box>
      <Box mt={2}>
        <Typography variant="body2">请上传 PDF 文件。</Typography>
      </Box>
      <Box mt={2}>
        <Table>
          <TableHead>
            <TableRow><TableCell>ID</TableCell><TableCell>文件名</TableCell><TableCell>水印</TableCell><TableCell>操作</TableCell></TableRow>
          </TableHead>
          <TableBody>
            {docs.map(d => (
              <TableRow key={d.id}>
                <TableCell>{d.id}</TableCell>
                <TableCell>{d.filename}</TableCell>
                <TableCell>{String(d.watermark_enabled)}</TableCell>
                <TableCell><Button size="small" color="error" onClick={()=>setConfirmDelete({ open:true, id: d.id })}>删除</Button></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>

      <Snackbar open={snack.open} autoHideDuration={4000} onClose={()=>setSnack(s=>({...s, open:false}))}>
        <Alert severity={snack.severity} onClose={()=>setSnack(s=>({...s, open:false}))}>{snack.message}</Alert>
      </Snackbar>

      <Dialog open={confirmDelete.open} onClose={()=>setConfirmDelete({ open:false, id:null })}>
        <DialogTitle>确认删除文档？</DialogTitle>
        <DialogActions>
          <Button onClick={()=>setConfirmDelete({ open:false, id:null })}>取消</Button>
          <Button color="error" onClick={()=>doDelete(confirmDelete.id)}>删除</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
import React, { useEffect, useState } from 'react'
import { Box, Typography, Button, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material'
import api from '../../utils/api'

export default function AdminDocuments(){
  const [docs, setDocs] = useState([])
  const [file, setFile] = useState(null)
  const [watermark, setWatermark] = useState(true)

  async function load(){
    const r = await api.get('/api/documents')
    setDocs(r.data.items || [])
  }

  useEffect(()=>{ load() }, [])

  async function upload(){
    if(!file) return
    const fd = new FormData()
    fd.append('file', file)
    fd.append('watermark_enabled', watermark)
    try{
      await api.post('/api/documents/upload', fd, { headers: {'Content-Type': 'multipart/form-data'} })
      import { Snackbar, Alert, CircularProgress, Dialog, DialogTitle, DialogActions } from '@mui/material'
      setFile(null)
      load()
    }catch(e){ alert('上传失败') }
  }
        const [loading, setLoading] = useState(false)
        const [snack, setSnack] = useState({ open: false, severity: 'info', message: '' })
        const [confirmDelete, setConfirmDelete] = useState({ open: false, id: null })

  async function deleteDoc(id){
    if(!window.confirm('确认删除文档？')) return
    await api.delete(`/api/documents/${id}`)
    load()
  }

  return (
    <Box mt={4}>
                <Button variant="contained" onClick={upload} disabled={loading}>{loading ? <CircularProgress size={16} /> : '上传'}</Button>
      <Box mt={2}>
        <Box display="flex" gap={2} alignItems="center">
          <input type="file" accept="application/pdf" onChange={e=>setFile(e.target.files[0])} />
          <Button variant="contained" onClick={upload}>上传</Button>
        </Box>
        <Box mt={2}>
          <Typography variant="body2">请上传 PDF 文件。</Typography>
        </Box>
                  <TableRow><TableCell>ID</TableCell><TableCell>文件名</TableCell><TableCell>水印</TableCell><TableCell>操作</TableCell></TableRow>
      <Box mt={2}>
        <Table>
          <TableHead>
            <TableRow><TableCell>ID</TableCell><TableCell>文件名</TableCell><TableCell>水印</TableCell><TableCell>操作</TableCell></TableRow>
          </TableHead>
          <TableBody>
            {docs.map(d => (
                      <TableCell><Button size="small" color="error" onClick={()=>setConfirmDelete({ open:true, id: d.id })}>删除</Button></TableCell>
                <TableCell>{d.id}</TableCell>
                <TableCell>{d.filename}</TableCell>
                <TableCell>{String(d.watermark_enabled)}</TableCell>
                <TableCell>
                  <Button size="small" color="error" onClick={()=>deleteDoc(d.id)}>删除</Button>
            <Snackbar open={snack.open} autoHideDuration={4000} onClose={()=>setSnack(s=>({...s, open:false}))}>
              <Alert severity={snack.severity} onClose={()=>setSnack(s=>({...s, open:false}))}>{snack.message}</Alert>
            </Snackbar>
            <Dialog open={confirmDelete.open} onClose={()=>setConfirmDelete({ open:false, id:null })}>
              <DialogTitle>确认删除文档？</DialogTitle>
              <DialogActions>
                <Button onClick={()=>setConfirmDelete({ open:false, id:null })}>取消</Button>
                <Button color="error" onClick={async ()=>{ const id = confirmDelete.id; setConfirmDelete({ open:false, id:null }); setLoading(true); try{ await api.delete(`/api/documents/${id}`); setSnack({ open:true, severity:'success', message:'文档已删除' }); load(); }catch(e){ setSnack({ open:true, severity:'error', message: e.response?.data?.detail || e.message }); } finally{ setLoading(false); } }}>删除</Button>
              </DialogActions>
            </Dialog>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>
    </Box>
  )
}
