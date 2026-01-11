import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { CssBaseline, Container, Box, Typography } from '@mui/material'
import DocList from './pages/DocList'
import DownloadLogs from './pages/DownloadLogs'
import ExportHistory from './pages/ExportHistory'
import UserLogin from './pages/UserLogin'
import UserDocs from './pages/UserDocs'
import RequireAuth from './components/RequireAuth'
import RequireAdmin from './components/RequireAdmin'
import LogoutButton from './components/LogoutButton'
import SessionMonitor from './components/SessionMonitor'
import { useState } from 'react'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminUsers from './pages/admin/AdminUsers'
import AdminDocuments from './pages/admin/AdminDocuments'
import AdminGroups from './pages/admin/AdminGroups'
import api from './utils/api'
import AdminAudit from './pages/admin/AdminAudit'

function App(){
  async function handleLogin(token, username){
    localStorage.setItem('token', token)
    localStorage.setItem('username', username)
    try{
      const r = await api.get('/api/users/me')
      localStorage.setItem('is_admin', r.data.is_admin ? 'true' : 'false')
    }catch(e){ localStorage.setItem('is_admin', 'false') }
    window.location.href = '/user'
  }

  return (
    <BrowserRouter>
      <CssBaseline />
      <Container maxWidth="md">
          <Box display="flex" justifyContent="space-between" alignItems="center" py={2}>
          <Typography variant="h6">SecureHub</Typography>
          <Box display="flex" gap={2} alignItems="center">
            <SessionMonitor />
            {localStorage.getItem('token') ? (
              <Box display="flex" gap={2} alignItems="center">
                <Typography variant="body2">{localStorage.getItem('username') || ''}</Typography>
                <LogoutButton />
              </Box>
            ) : null}
          </Box>
        </Box>
        <Routes>
          <Route path="/" element={<DocList />} />
          <Route path="/logs" element={<DownloadLogs />} />
          <Route path="/exports" element={<ExportHistory />} />
          <Route path="/login" element={<UserLogin onLogin={handleLogin} />} />
          <Route path="/user" element={<RequireAuth><UserDocs token={localStorage.getItem('token')} /></RequireAuth>} />
          <Route path="/admin" element={<RequireAdmin><AdminDashboard /></RequireAdmin>} />
          <Route path="/admin/users" element={<RequireAdmin><AdminUsers /></RequireAdmin>} />
          <Route path="/admin/documents" element={<RequireAdmin><AdminDocuments /></RequireAdmin>} />
          <Route path="/admin/groups" element={<RequireAdmin><AdminGroups /></RequireAdmin>} />
          <Route path="/admin/audit" element={<RequireAdmin><AdminAudit /></RequireAdmin>} />
        </Routes>
      </Container>
    </BrowserRouter>
  )
}

export default App
