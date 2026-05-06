import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from './components/ui/card';
import { Button } from './components/ui/button';
import { Pill, RefreshCw, AlertCircle, Plus, Pencil, Trash2, Coffee, Utensils, Soup, FileText, Moon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function Dashboard({
    medicines,
    loading,
    syncing,
    downloadReport,
    consumePeriod,
    openNewMedicine,
    openEditMedicine,
    handleDelete
}) {
    const navigate = useNavigate();
    const [selectedPeriod, setSelectedPeriod] = React.useState(null);
    const [activeRowId, setActiveRowId] = React.useState(null);

    const getMedicinesForPeriod = (period) => {
        return medicines.filter(m => m.periods.includes(period));
    };

    const periods = [
        { id: 'cafe', label: 'Café da Manhã', icon: Coffee, color: 'text-yellow-400' },
        { id: 'almoco', label: 'Almoço', icon: Utensils, color: 'text-orange-400' },
        { id: 'jantar', label: 'Jantar', icon: Soup, color: 'text-green-400' },
        { id: 'dormir', label: 'Dormir', icon: Moon, color: 'text-blue-400' },
    ];

    const filteredMedicines = selectedPeriod
        ? medicines.filter(m => m.periods.includes(selectedPeriod))
        : medicines;

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
                            <Card
                                key={period.id}
                                className="border-[rgb(var(--border))] bg-[rgb(var(--surface))] cursor-pointer hover:bg-[rgb(var(--surface))]/80 transition-colors"
                                onClick={() => navigate(`/period/${period.id}`)}
                            >
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
                            </Card>
                        );
                    })}
                </div>

                {/* Inventory List */}
                <Card className="border-[rgb(var(--border))] bg-[rgb(var(--surface))]">
                    <CardHeader className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                        <CardTitle className="text-white">Estoque Completo</CardTitle>
                        <div className="flex flex-wrap gap-2">
                            <Button
                                variant={selectedPeriod === null ? "secondary" : "ghost"}
                                size="sm"
                                onClick={() => setSelectedPeriod(null)}
                                className={selectedPeriod === null ? "bg-[rgb(var(--primary))] text-white hover:bg-[rgb(var(--primary))]/90" : "text-[rgb(var(--muted))] hover:text-white hover:bg-[rgb(var(--surface))]"}
                            >
                                Todos
                            </Button>
                            {periods.map(p => (
                                <Button
                                    key={p.id}
                                    variant={selectedPeriod === p.id ? "secondary" : "ghost"}
                                    size="sm"
                                    onClick={() => setSelectedPeriod(p.id)}
                                    className={selectedPeriod === p.id
                                        ? `bg-${p.color.split('-')[1]}-400/20 text-${p.color.split('-')[1]}-400 border border-${p.color.split('-')[1]}-400/20`
                                        : "text-[rgb(var(--muted))] hover:text-white hover:bg-[rgb(var(--surface))]"
                                    }
                                >
                                    {p.label}
                                </Button>
                            ))}
                            <Button size="sm" onClick={openNewMedicine} className="ml-2">
                                <Plus className="h-4 w-4 mr-2" /> Novo
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {filteredMedicines.length === 0 ? (
                                <div className="text-center py-8 text-[rgb(var(--muted))]">
                                    Nenhum medicamento encontrado para este filtro.
                                </div>
                            ) : (
                                filteredMedicines.map((med) => (
                                    <div 
                                        key={med.id} 
                                        onClick={() => setActiveRowId(activeRowId === med.id ? null : med.id)}
                                        className={`flex items-center justify-between border-b border-[rgb(var(--border))] box-border p-4 -mx-4 rounded-xl last:border-0 cursor-pointer transition-all duration-200 ${
                                            activeRowId === med.id 
                                                ? 'bg-[rgb(var(--primary))]/20 shadow-[0_0_15px_rgba(var(--primary),0.1)] border-transparent' 
                                                : 'hover:bg-[rgb(var(--surface))]'
                                        }`}
                                    >
                                        <div className="space-y-1">
                                            <p className="font-medium text-white leading-none">{med.name}</p>
                                            <p className="text-sm text-[rgb(var(--muted))]">
                                                {med.dosage} • {med.substance}
                                            </p>
                                            <div className="flex gap-2 mt-1">
                                                {med.periods.map(p => {
                                                    const periodColors = {
                                                        'cafe': 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
                                                        'almoco': 'text-orange-400 bg-orange-400/10 border-orange-400/20',
                                                        'jantar': 'text-green-400 bg-green-400/10 border-green-400/20',
                                                        'dormir': 'text-blue-400 bg-blue-400/10 border-blue-400/20',
                                                    };
                                                    const colorClass = periodColors[p] || 'text-[rgb(var(--muted))] bg-[rgb(var(--border))]';

                                                    return (
                                                        <span key={p} className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border ${colorClass}`}>
                                                            {p}
                                                        </span>
                                                    );
                                                })}
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
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
