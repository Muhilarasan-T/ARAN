import { Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import DemoPage from './pages/DemoPage'
import ProtectPage from './pages/ProtectPage'
import ResultPage from './pages/ResultPage'

export default function App() {
    return (
        <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/demo" element={<DemoPage />} />
            <Route path="/protect" element={<ProtectPage />} />
            <Route path="/result" element={<ResultPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    )
}
