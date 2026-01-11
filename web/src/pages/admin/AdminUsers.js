import React, { useEffect, useState } from 'react'
import { Box, Typography, Button, TextField, Table, TableBody, TableCell, TableHead, TableRow, Snackbar, Alert, CircularProgress, Dialog, DialogTitle, DialogActions } from '@mui/material'
import api from '../../utils/api'

export default function AdminUsers(){
  const [users, setUsers] = useState([])
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [usernameError, setUsernameError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [page, setPage] = useState(1)
  const [size] = useState(10)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [snack, setSnack] = useState({ open: false, severity: 'info', message: '' })
  const [confirmDelete, setConfirmDelete] = useState({ open: false, id: null })

  async function load(p = 1){
    setLoading(true)
    try{
      const r = await api.get('/api/users', { params: { page: p, size } })
      setUsers(r.data.items || [])
      setTotal(r.data.total || 0)
      setPage(r.data.page || p)
    }catch(e){
      setSnack({ open: true, severity: 'error', message: e.response?.data?.detail || e.message })
    }finally{ setLoading(false) }
  }

  useEffect(()=>{ load(1) }, [])

  async function create(){
    // client-side validation
    setUsernameError('')
    setPasswordError('')
    if(!username || username.trim().length === 0){ setUsernameError('用户名不能为空'); return }
    if(!password || password.length < 8){ setPasswordError('密码至少8位'); return }
    setLoading(true)
    try{
      await api.post('/api/users', { username, password })
      setUsername(''); setPassword('')
      setSnack({ open: true, severity: 'success', message: '用户已创建' })
      load(1)
    }catch(e){
      setSnack({ open: true, severity: 'error', message: e.response?.data?.detail || e.message })
    }finally{ setLoading(false) }
  }

  async function removeUser(id){
    setConfirmDelete({ open: true, id })
  }

  async function doRemove(){
    const id = confirmDelete.id
    setConfirmDelete({ open: false, id: null })
    setLoading(true)
    try{
      await api.delete(`/api/users/${id}`)
      setSnack({ open: true, severity: 'success', message: '用户已删除' })
      load(page)
    }catch(e){
      setSnack({ open: true, severity: 'error', message: e.response?.data?.detail || e.message })
    }finally{ setLoading(false) }
  }

  async function toggleActive(u){
    setLoading(true)
    try{
      await api.put(`/api/users/${u.id}/active`, { active: !u.is_active })
      setSnack({ open: true, severity: 'success', message: '状态已切换' })
      load(page)
    }catch(e){ setSnack({ open: true, severity: 'error', message: e.response?.data?.detail || e.message }) }finally{ setLoading(false) }
  }

  async function toggleAdmin(u){
    setLoading(true)
    try{
      await api.put(`/api/users/${u.id}/admin`, { is_admin: !u.is_admin })
      setSnack({ open: true, severity: 'success', message: '管理员权限已切换' })
      load(page)
    }catch(e){ setSnack({ open: true, severity: 'error', message: e.response?.data?.detail || e.message }) }finally{ setLoading(false) }
  }

  return (
    <Box mt={4}>
      <Typography variant="h5">用户管理</Typography>
      <Box mt={2} display="flex" gap={2} alignItems="center">
        <TextField label="用户名" value={username} onChange={e=>setUsername(e.target.value)} error={!!usernameError} helperText={usernameError} />
        <TextField label="密码" type="password" value={password} onChange={e=>setPassword(e.target.value)} error={!!passwordError} helperText={passwordError} />
        <Button variant="contained" onClick={create} disabled={loading}>创建用户</Button>
      </Box>
      <Box mt={3}>
        <Table>
          <TableHead>
            <TableRow><TableCell>ID</TableCell><TableCell>用户名</TableCell><TableCell>Active</TableCell><TableCell>Admin</TableCell><TableCell>操作</TableCell></TableRow>
          </TableHead>
          <TableBody>
            {users.map(u => (
              <TableRow key={u.id}>
                <TableCell>{u.id}</TableCell>
                <TableCell>{u.username}</TableCell>
                <TableCell>{String(u.is_active)}</TableCell>
                <TableCell>{String(u.is_admin)}</TableCell>
                <TableCell>
                  <Button size="small" onClick={()=>toggleActive(u)} disabled={loading}>{loading ? <CircularProgress size={16} /> : '切换Active'}</Button>
                  <Button size="small" onClick={()=>toggleAdmin(u)} disabled={loading}>{loading ? <CircularProgress size={16} /> : '切换Admin'}</Button>
                  <Button size="small" color="error" onClick={()=>removeUser(u.id)} disabled={loading}>{loading ? <CircularProgress size={16} /> : '删除'}</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {loading && <Box mt={2}><CircularProgress /></Box>}
        <Box mt={2} display="flex" gap={2} alignItems="center">
          <Button disabled={page<=1} onClick={()=>load(page-1)}>上一页</Button>
          <Typography>第 {page} 页 / 共 {Math.ceil(total/size)||1} 页</Typography>
          <Button disabled={page*size>=total} onClick={()=>load(page+1)}>下一页</Button>
        </Box>
      </Box>
      <Snackbar open={snack.open} autoHideDuration={4000} onClose={()=>setSnack(s=>({...s, open:false}))}>
        <Alert severity={snack.severity} onClose={()=>setSnack(s=>({...s, open:false}))}>{snack.message}</Alert>
      </Snackbar>
      <Dialog open={confirmDelete.open} onClose={()=>setConfirmDelete({ open:false, id:null })}>
        <DialogTitle>确认删除用户？</DialogTitle>
        <DialogActions>
          <Button onClick={()=>setConfirmDelete({ open:false, id:null })}>取消</Button>
          <Button color="error" onClick={doRemove}>删除</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
