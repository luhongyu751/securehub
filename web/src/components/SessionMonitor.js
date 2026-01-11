import React, { useEffect, useState } from 'react'
import { Box, Typography, Dialog, DialogTitle, DialogContent, DialogActions, Button } from '@mui/material'
import api from '../utils/api'

function parseJwtPayload(token){
  try{
    const parts = token.split('.')
    if(parts.length !== 3) return null
    const b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const padded = b64.padEnd(Math.ceil(b64.length/4)*4, '=')
    const json = atob(padded)
    return JSON.parse(json)
  }catch(e){ return null }
}

export default function SessionMonitor(){
  const [remaining, setRemaining] = useState(null)
  const [openWarn, setOpenWarn] = useState(false)

  useEffect(()=>{
    let mounted = true
    function tick(){
      const token = localStorage.getItem('token')
      if(!token){ setRemaining(null); setOpenWarn(false); return }
      const payload = parseJwtPayload(token)
      if(!payload || !payload.exp){ setRemaining(null); return }
      const left = Math.max(0, Math.floor(payload.exp - Date.now()/1000))
      if(mounted) setRemaining(left)
      // Only show dialog after expiration (left === 0). Do not auto-logout here.
      if(left === 0){
        if(mounted) setOpenWarn(true)
      }
    }

    tick()
    const id = setInterval(tick, 1000)
    return ()=>{ mounted = false; clearInterval(id) }
  }, [])

  async function extendSession(){
    try{
      const r = await api.post('/api/token/refresh')
      const newToken = r.data.access_token
      localStorage.setItem('token', newToken)
      setOpenWarn(false)
    }catch(e){
      // refresh failed: logout
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      window.location.href = '/login'
    }
  }

  function logout(){
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    window.location.href = '/login'
  }

  return (
    <>
      <Box>
        {remaining !== null && (
          <Typography variant="body2">会话剩余: {Math.floor(remaining/60)}m {remaining%60}s</Typography>
        )}
      </Box>
      <Dialog open={openWarn} onClose={(e, reason)=>{ /* prevent backdrop/esc close */ }} disableEscapeKeyDown>
        <DialogTitle>会话已过期</DialogTitle>
        <DialogContent>
          <Typography>会话已过期，请重新登录。</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={logout} variant="contained">登出</Button>
        </DialogActions>
      </Dialog>
    </>
  )
}
