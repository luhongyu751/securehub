import React from 'react'
import { Box, Typography } from '@mui/material'

export default function AdminDashboard(){
  return (
    <Box mt={4}>
      <Typography variant="h5">管理员面板</Typography>
      <Typography variant="body2" mt={2}>快速入口：用户管理、文档管理、组管理与审计日志。</Typography>
    </Box>
  )
}
