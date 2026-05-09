import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ReactFlowProvider } from '@xyflow/react'
import Home from './pages/Home'
import Editor from './pages/Editor'

export default function App() {
  return (
    <ReactFlowProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/editor/:id" element={<Editor />} />
          <Route path="/editor" element={<Editor />} />
        </Routes>
      </BrowserRouter>
    </ReactFlowProvider>
  )
}
