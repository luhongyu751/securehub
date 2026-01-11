import React, { useEffect, useState } from 'react'
import { Box, Typography, Button, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material'
import api from '../../utils/api'

export default function AdminAudit(){
  const [items, setItems] = useState([])

  async function load(){
    const r = await api.get('/api/audit')
    setItems(r.data.items || [])
  }

  useEffect(()=>{ load() }, [])

  return (
    <Box mt={4}>
      <Typography variant="h5">审计日志</Typography>
      <Box mt={2}>
        <Button variant="outlined" href="/api/audit/export">导出 CSV</Button>
      </Box>
      <Box mt={2}>
        <Table>
          <TableHead>
            <TableRow><TableCell>时间</TableCell><TableCell>操作者</TableCell><TableCell>动作</TableCell><TableCell>对象</TableCell><TableCell>详情</TableCell></TableRow>
          </TableHead>
          <TableBody>
            {items.map(it => (
              <TableRow key={it.id}><TableCell>{it.timestamp}</TableCell><TableCell>{it.actor || it.actor_id}</TableCell><TableCell>{it.action}</TableCell><TableCell>{(it.object_type||'') + ':' + (it.object_id||'')}</TableCell><TableCell>{it.detail}</TableCell></TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>
    </Box>
  )
}
