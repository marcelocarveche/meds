import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MedicineDialog } from './components/MedicineDialog';
import { Dashboard } from './Dashboard';
import { PeriodPage } from './PeriodPage';

const API_URL = 'http://localhost:8000';

function App() {
    const [medicines, setMedicines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [syncing, setSyncing] = useState(false);

    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [editingMedicine, setEditingMedicine] = useState(null);

    const downloadReport = () => {
        window.open(`${API_URL}/report/html`, '_blank');
    };

    useEffect(() => {
        fetchMedicines();
    }, []);

    const fetchMedicines = async () => {
        try {
            const res = await fetch(`${API_URL}/medicines`);
            const data = await res.json();
            setMedicines(data);
            setLoading(false);
        } catch (error) {
            console.error("Failed to fetch medicines", error);
            setLoading(false);
        }
    };

    const consumePeriod = async (period) => {
        setSyncing(true);
        try {
            if (period === 'sync') {
                await fetch(`${API_URL}/sync`);
            } else {
                await fetch(`${API_URL}/consume/${period}`, { method: 'POST' });
            }
            await fetchMedicines(); // Refresh data
        } catch (error) {
            console.error("Failed to consume", error);
        } finally {
            setSyncing(false);
        }
    };

    const handleSaveMedicine = async (medicine) => {
        // If editing
        const method = editingMedicine ? 'PUT' : 'POST';
        const url = editingMedicine
            ? `${API_URL}/medicines/${medicine.id}`
            : `${API_URL}/medicines`;

        try {
            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(medicine)
            });

            if (res.ok) {
                await fetchMedicines();
                setIsDialogOpen(false);
                setEditingMedicine(null);
            }
        } catch (error) {
            console.error("Failed to save", error);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Tem certeza que deseja excluir este medicamento?')) return;

        try {
            await fetch(`${API_URL}/medicines/${id}`, { method: 'DELETE' });
            await fetchMedicines();
        } catch (error) {
            console.error("Failed to delete", error);
        }
    };

    const openNewMedicine = () => {
        setEditingMedicine(null);
        setIsDialogOpen(true);
    }

    const openEditMedicine = (med) => {
        setEditingMedicine(med);
        setIsDialogOpen(true);
    }

    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={
                    <Dashboard
                        medicines={medicines}
                        loading={loading}
                        syncing={syncing}
                        downloadReport={downloadReport}
                        consumePeriod={consumePeriod}
                        openNewMedicine={openNewMedicine}
                        openEditMedicine={openEditMedicine}
                        handleDelete={handleDelete}
                    />
                } />
                <Route path="/period/:periodId" element={
                    <PeriodPage
                        medicines={medicines}
                        consumePeriod={consumePeriod}
                        syncing={syncing}
                    />
                } />
            </Routes>

            <MedicineDialog
                isOpen={isDialogOpen}
                onClose={() => setIsDialogOpen(false)}
                onSave={handleSaveMedicine}
                medicine={editingMedicine}
            />
        </BrowserRouter>
    );
}

export default App;
