import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from './components/ui/card';
import { Button } from './components/ui/button';
import { ArrowLeft, Check, Coffee, Utensils, Soup, Moon, AlertCircle } from 'lucide-react';

export function PeriodPage({ medicines, consumePeriod, syncing }) {
    const { periodId } = useParams();
    const navigate = useNavigate();

    const periods = {
        'cafe': { label: 'Café da Manhã', icon: Coffee, color: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/20' },
        'almoco': { label: 'Almoço', icon: Utensils, color: 'text-orange-400', bg: 'bg-orange-400/10', border: 'border-orange-400/20' },
        'jantar': { label: 'Jantar', icon: Soup, color: 'text-green-400', bg: 'bg-green-400/10', border: 'border-green-400/20' },
        'dormir': { label: 'Dormir', icon: Moon, color: 'text-blue-400', bg: 'bg-blue-400/10', border: 'border-blue-400/20' },
    };

    const periodConfig = periods[periodId];

    if (!periodConfig) {
        return <div className="p-8 text-white">Período não encontrado.</div>;
    }

    const Icon = periodConfig.icon;
    const periodMeds = medicines.filter(m => m.periods.includes(periodId));

    const handleConsumeAll = async () => {
        await consumePeriod(periodId);
        navigate('/'); // Go back to dashboard after consuming? Or stay? Maybe stay to show updated stock.
    };

    return (
        <div className="min-h-screen bg-[rgb(var(--background))] p-8 text-[rgb(var(--text))]">
            <div className="mx-auto max-w-3xl space-y-8">

                {/* Header */}
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
                        <ArrowLeft className="h-6 w-6 text-white" />
                    </Button>
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-full ${periodConfig.bg}`}>
                            <Icon className={`h-6 w-6 ${periodConfig.color}`} />
                        </div>
                        <h1 className="text-3xl font-bold tracking-tight text-white">
                            {periodConfig.label}
                        </h1>
                    </div>
                </div>

                {/* Main Card */}
                <Card className="border-[rgb(var(--border))] bg-[rgb(var(--surface))]">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-lg font-medium text-[rgb(var(--muted))]">
                            Medicamentos para tomar
                        </CardTitle>
                        <span className="text-2xl font-bold text-white">{periodMeds.length} total</span>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {periodMeds.length === 0 ? (
                                <div className="text-center py-8 text-[rgb(var(--muted))]">
                                    Nenhum medicamento para este período.
                                </div>
                            ) : (
                                periodMeds.map((med) => (
                                    <div key={med.id} className="flex items-center justify-between border-b border-[rgb(var(--border))] pb-4 last:border-0 last:pb-0">
                                        <div className="space-y-1">
                                            <p className="font-medium text-white text-lg">{med.name}</p>
                                            <p className="text-sm text-[rgb(var(--muted))]">
                                                {med.dosage} {med.substance && `• ${med.substance}`}
                                            </p>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            {med.quantity < 5 && (
                                                <div className="flex items-center text-red-400 text-xs font-bold bg-red-400/10 px-2 py-1 rounded">
                                                    <AlertCircle className="w-3 h-3 mr-1" />
                                                    {med.quantity} restante
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                    <CardFooter className="pt-6">
                        <Button
                            className="w-full h-12 text-lg bg-[rgb(var(--primary))]"
                            onClick={handleConsumeAll}
                            disabled={periodMeds.length === 0 || syncing}
                        >
                            {syncing ? 'Registrando...' : 'Confirmar Consumo de Todos'}
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        </div>
    );
}
