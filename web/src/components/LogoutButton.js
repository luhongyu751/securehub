import React from 'react'
import { Button } from '@mui/material'

export default function LogoutButton(){
  function logout(){
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    window.location.href = '/login'
  }

  return <Button variant="outlined" onClick={logout}>登出</Button>
}
