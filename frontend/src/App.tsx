import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import InvoiceListPage from './pages/InvoiceListPage';
import InvoiceDetailPage from './pages/InvoiceDetailPage';
import UploadPage from './pages/UploadPage';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<InvoiceListPage />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="invoices/:id" element={<InvoiceDetailPage />} />
      </Route>
    </Routes>
  );
}
