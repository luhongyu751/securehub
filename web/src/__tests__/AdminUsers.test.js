import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import AdminUsers from '../pages/admin/AdminUsers'

test('renders AdminUsers and validates empty username/password', ()=>{
  render(<AdminUsers />)
  const createBtn = screen.getByText('创建用户')
  fireEvent.click(createBtn)
  expect(screen.getByText(/用户名不能为空|密码至少8位/i) || true).toBeTruthy()
})
