import React, { useEffect, useState } from 'react'
import { Box, Typography, TextField, Button, Table, TableBody, TableCell, TableHead, TableRow, Snackbar, Alert, CircularProgress } from '@mui/material'
import api from '../../utils/api'

export default function AdminGroups(){
  const [groups, setGroups] = useState([])
  const [name, setName] = useState('')
  const [users, setUsers] = useState([])
  const [selectedGroup, setSelectedGroup] = useState(null)
  const [selectedUser, setSelectedUser] = useState(null)
  const [loading, setLoading] = useState(false)
  const [snack, setSnack] = useState({ open: false, severity: 'info', message: '' })

  async function load(){
    try{
      const r = await api.get('/api/groups')
      setGroups(r.data.items || [])
    }catch(e){ setGroups([]) }
    try{
      const ru = await api.get('/api/users')
      setUsers(ru.data.items || [])
    }catch(e){ setUsers([]) }
  }

  useEffect(()=>{ load() }, [])

  async function create(){
    setLoading(true)
    try{
      if(!name || name.trim().length === 0){ setSnack({ open:true, severity:'error', message:'组名不能为空' }); return }
      await api.post('/api/groups', { name })
      setName('')
      setSnack({ open: true, severity: 'success', message: '组已创建' })
      load()
    }catch(e){ setSnack({ open:true, severity:'error', message: e.response?.data?.detail || e.message }) }finally{ setLoading(false) }
  }

  async function addUser(){
    if(!selectedGroup || !selectedUser){ setSnack({ open:true, severity:'error', message:'请选择组与用户' }); return }
    setLoading(true)
    try{
      await api.post(`/api/groups/${selectedGroup}/add_user`, { user_id: selectedUser })
      setSnack({ open:true, severity:'success', message:'用户已添加' })
      load()
    }catch(e){ setSnack({ open:true, severity:'error', message: e.response?.data?.detail || e.message }) }finally{ setLoading(false) }
  }

  async function removeUser(){
    if(!selectedGroup || !selectedUser){ setSnack({ open:true, severity:'error', message:'请选择组与用户' }); return }
    setLoading(true)
    try{
      await api.post(`/api/groups/${selectedGroup}/remove_user`, { user_id: selectedUser })
      setSnack({ open:true, severity:'success', message:'用户已移除' })
      load()
    }catch(e){ setSnack({ open:true, severity:'error', message: e.response?.data?.detail || e.message }) }finally{ setLoading(false) }
  }

  return (
    <Box mt={4}>
      <Typography variant="h5">组管理</Typography>
      <Box mt={2} display="flex" gap={2} alignItems="center">
        <TextField label="组名" value={name} onChange={e=>setName(e.target.value)} />
        <Button variant="contained" onClick={create}>创建组</Button>
      </Box>
      <Box mt={2} display="flex" gap={2} alignItems="center">
        <TextField select value={selectedGroup||''} onChange={e=>setSelectedGroup(e.target.value)} SelectProps={{ native: true }}>
          <option value="">选择组</option>
          {groups.map(g=> <option key={g.id} value={g.id}>{g.name}</option>)}
        </TextField>
        <TextField select value={selectedUser||''} onChange={e=>setSelectedUser(e.target.value)} SelectProps={{ native: true }}>
          <option value="">选择用户</option>
          {users.map(u=> <option key={u.id} value={u.id}>{u.username}</option>)}
        </TextField>
        <Button variant="contained" onClick={addUser}>添加用户到组</Button>
        <Button variant="outlined" onClick={removeUser}>从组移除用户</Button>
      </Box>
      <Box mt={3}>
        <Table>
          <TableHead>
            <TableRow><TableCell>组名</TableCell><TableCell>成员数</TableCell><TableCell>成员</TableCell></TableRow>
          </TableHead>
          <TableBody>
            {groups.map(g => (
              <TableRow key={g.id}>
                <TableCell>{g.name}</TableCell>
                <TableCell>{g.members.length}</TableCell>
                <TableCell>{g.members.map(m=>m.username).join(', ')}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {loading && <Box mt={2}><CircularProgress /></Box>}
        <Snackbar open={snack.open} autoHideDuration={4000} onClose={()=>setSnack(s=>({...s, open:false}))}>
          <Alert severity={snack.severity} onClose={()=>setSnack(s=>({...s, open:false}))}>{snack.message}</Alert>
        </Snackbar>
      </Box>
    </Box>
  )
}
