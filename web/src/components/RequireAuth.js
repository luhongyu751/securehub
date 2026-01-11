import React from 'react'
import { Navigate } from 'react-router-dom'

function parseJwtPayload(token){
  try{
    const parts = token.split('.')
    if(parts.length !== 3) return null
    const b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const padded = b64.padEnd(Math.ceil(b64.length/4)*4, '=')
    const json = atob(padded)
    return JSON.parse(json)
  }catch(e){
    return null
  }
}

export default function RequireAuth({ children }){
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  if(!token) return <Navigate to="/login" replace />

  const payload = parseJwtPayload(token)
  if(payload && payload.exp && Date.now() / 1000 >= payload.exp){
    // token expired: clear and redirect to login
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    return <Navigate to="/login" replace />
  }

  return children
}
