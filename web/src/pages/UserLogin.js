import React, { useState } from 'react'
import { Box, TextField, Button, Typography } from '@mui/material'
import api from '../utils/api'

export default function UserLogin({ onLogin }){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [otp, setOtp] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e){
    e.preventDefault()
    setLoading(true)
    setError(null)
    try{
      const passwordField = otp ? `${password}:${otp}` : password
      const params = new URLSearchParams()
      params.append('username', username)
      params.append('password', passwordField)
      const resp = await api.post('/api/token', params)
      const token = resp.data.access_token
      // refresh token is set as HttpOnly cookie by server
      onLogin(token, username)
    }catch(err){
      setError(err.response?.data?.detail || err.message)
    }finally{ setLoading(false) }
  }

  return (
    <Box maxWidth={420} mx="auto" mt={6}>
      <Typography variant="h5" mb={2}>用户登录</Typography>
      <form onSubmit={handleSubmit}>
        <TextField label="用户名" value={username} onChange={e=>setUsername(e.target.value)} fullWidth margin="normal" />
        <TextField label="密码" type="password" value={password} onChange={e=>setPassword(e.target.value)} fullWidth margin="normal" />
        <TextField label="2FA OTP（可选）" value={otp} onChange={e=>setOtp(e.target.value)} fullWidth margin="normal" />
        {error && <Typography color="error">{error}</Typography>}
        <Box mt={2} display="flex" gap={2}>
          <Button type="submit" variant="contained" disabled={loading}>登录</Button>
        </Box>
      </form>
    </Box>
  )
}
