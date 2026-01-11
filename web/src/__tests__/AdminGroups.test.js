import React from 'react'
import { render, screen } from '@testing-library/react'
import AdminGroups from '../pages/admin/AdminGroups'

test('renders AdminGroups create UI', ()=>{
  render(<AdminGroups />)
  expect(screen.getByText(/组管理/i)).toBeTruthy()
})
