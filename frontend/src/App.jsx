import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from './components/ui/card';
import { Button } from './components/ui/button';
import { Pill, Sun, Moon, Sunrise, Sunset, RefreshCw, AlertCircle, Plus, Pencil, Trash2, Coffee, Utensils, Soup, FileText } from 'lucide-react';
import { MedicineDialog } from './components/MedicineDialog';

const API_URL = 'http://localhost:8000';

function App() {
    const [medicines, setMedicines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [syncing, setSyncing] = useState(false);

    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [editingMedicine, setEditingMedicine] = useState(null);

    const downloadReport = () => {
        window.open(`${API_URL}/report`, '_blank');
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

    const getMedicinesForPeriod = (period) => {
        return medicines.filter(m => m.periods.includes(period));
    };

    const periods = [
        { id: 'cafe', label: 'Café da Manhã', icon: Coffee, color: 'text-yellow-400' },
        { id: 'almoco', label: 'Almoço', icon: Utensils, color: 'text-orange-400' },
        { id: 'jantar', label: 'Jantar', icon: Soup, color: 'text-green-400' },
        { id: 'dormir', label: 'Dormir', icon: Moon, color: 'text-blue-400' },
    ];

    if (loading) return <div className="flex h-screen items-center justify-center bg-[rgb(var(--background))] text-white">Carregando...</div>;

    return (
        <div className="min-h-screen bg-[rgb(var(--background))] p-8 text-[rgb(var(--text))]">
            <div className="mx-auto max-w-5xl space-y-8">

                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
                            <Pill className="h-8 w-8 text-[rgb(var(--primary))]" />
                            Medicamentos
                        </h1>
                        <p className="text-[rgb(var(--muted))]">Gerencie o estoque e o consumo diário.</p>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={downloadReport}>
                            <FileText className="mr-2 h-4 w-4" />
                            Relatório
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => consumePeriod('sync')} disabled={syncing}>
                            <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                            {syncing ? 'Sincronizando...' : 'Sincronizar Drive'}
                        </Button>
                    </div>
                </div>

                {/* Dashboard Grid */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    {periods.map((period) => {
                        const periodMeds = getMedicinesForPeriod(period.id);
                        const Icon = period.icon;

                        return (
                            <Card key={period.id} className="border-[rgb(var(--border))] bg-[rgb(var(--surface))]">
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium text-[rgb(var(--muted))]">
                                        {period.label}
                                    </CardTitle>
                                    <Icon className={`h-4 w-4 ${period.color}`} />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold text-white">{periodMeds.length} meds</div>
                                    <ul className="mt-2 space-y-1 text-xs text-[rgb(var(--muted))]">
                                        {periodMeds.map(m => (
                                            <li key={m.id} className="flex justify-between">
                                                <span>{m.name}</span>
                                                <span className={m.quantity < 10 ? 'text-red-400 font-bold' : ''}>
                                                    {m.quantity} un
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                </CardContent>
                                <CardFooter>
                                    <Button className="w-full bg-[rgb(var(--primary))]" onClick={() => consumePeriod(period.id)}>
                                        Consumir Todos
                                    </Button>
                                </CardFooter>
                            </Card>
                        );
                    })}
                </div>

                {/* Inventory List */}
                <Card className="border-[rgb(var(--border))] bg-[rgb(var(--surface))]">
                    <CardHeader className="flex items-center justify-between">
                        <CardTitle className="text-white">Estoque Completo</CardTitle>
                        <Button size="sm" onClick={openNewMedicine}>
                            <Plus className="h-4 w-4 mr-2" /> Novo Medicamento
                        </Button>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {medicines.map((med) => (
                                <div key={med.id} className="flex items-center justify-between border-b border-[rgb(var(--border))] pb-4 last:border-0 last:pb-0">
                                    <div className="space-y-1">
                                        <p className="font-medium text-white leading-none">{med.name}</p>
                                        <p className="text-sm text-[rgb(var(--muted))]">
                                            {med.dosage} • {med.substance}
                                        </p>
                                        <div className="flex gap-2 mt-1">
                                            {med.periods.map(p => (
                                                <span key={p} className="text-[10px] uppercase tracking-wider bg-[rgb(var(--border))] px-1.5 py-0.5 rounded text-[rgb(var(--muted))]">
                                                    {p}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-6">
                                        {med.quantity < 10 && (
                                            <div className="flex items-center text-red-400 text-xs font-bold bg-red-400/10 px-2 py-1 rounded">
                                                <AlertCircle className="w-3 h-3 mr-1" />
                                                Baixo
                                            </div>
                                        )}
                                        <div className="text-right">
                                            <p className="text-sm font-medium text-white">{med.quantity} unidades</p>
                                            <p className="text-xs text-[rgb(var(--muted))]">R$ {med.price || '0.00'}</p>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button variant="ghost" size="icon" className="h-8 w-8 text-[rgb(var(--muted))] hover:text-white" onClick={() => openEditMedicine(med)}>
                                                <Pencil className="h-4 w-4" />
                                            </Button>
                                            <Button variant="ghost" size="icon" className="h-8 w-8 text-red-400 hover:text-red-300 hover:bg-red-400/10" onClick={() => handleDelete(med.id)}>
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                <MedicineDialog
                    isOpen={isDialogOpen}
                    onClose={() => setIsDialogOpen(false)}
                    onSave={handleSaveMedicine}
                    medicine={editingMedicine}
                />
            </div>
        </div>
    );
}

export default App;
