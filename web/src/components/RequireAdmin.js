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

export default function RequireAdmin({ children }){
  if(typeof window === 'undefined') return <Navigate to="/login" replace />
  const token = localStorage.getItem('token')
  const isAdmin = localStorage.getItem('is_admin') === 'true'
  if(!token) return <Navigate to="/login" replace />
  const payload = parseJwtPayload(token)
  if(payload && payload.exp && Date.now() / 1000 >= payload.exp){
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('is_admin')
    return <Navigate to="/login" replace />
  }
  if(!isAdmin) return <Navigate to="/" replace />
  return children
}
