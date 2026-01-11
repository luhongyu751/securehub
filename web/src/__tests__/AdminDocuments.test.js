import React from 'react'
import { render, screen } from '@testing-library/react'
import AdminDocuments from '../pages/admin/AdminDocuments'

test('renders AdminDocuments upload button', ()=>{
  render(<AdminDocuments />)
  expect(screen.getByText(/上传/i)).toBeTruthy()
})
