import React, { useEffect, useState } from 'react'
import { Box, Typography, Table, TableHead, TableRow, TableCell, TableBody, Button } from '@mui/material'

const STORAGE_KEY = 'securehub_export_history'

function readHistory(){
  try{
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  }catch(e){ return [] }
}

function writeHistory(items){
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
}

export default function ExportHistory(){
  const [items, setItems] = useState([])

  useEffect(()=>{
    setItems(readHistory())
  }, [])

  function clearHistory(){
    writeHistory([])
    setItems([])
  }

  return (
    <Box mt={4}>
      <Typography variant="h4" gutterBottom>导出历史</Typography>
      <Box mb={2}><Button variant="outlined" onClick={clearHistory}>清除历史</Button></Box>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>时间</TableCell>
            <TableCell>筛选</TableCell>
            <TableCell>状态</TableCell>
            <TableCell>文件</TableCell>
            <TableCell>操作</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map(it => (
            <TableRow key={it.id}>
              <TableCell>{it.time}</TableCell>
              <TableCell>{JSON.stringify(it.filters)}</TableCell>
              <TableCell>{it.status}</TableCell>
              <TableCell>{it.filename || '-'}</TableCell>
              <TableCell>{it.downloadUrl ? <Button component="a" href={it.downloadUrl} target="_blank">下载</Button> : '-'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  )
}
