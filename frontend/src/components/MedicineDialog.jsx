import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from './ui/card';
import { X } from 'lucide-react';

export function MedicineDialog({ isOpen, onClose, onSave, medicine }) {
    const [formData, setFormData] = useState({
        id: '',
        name: '',
        substance: '',
        dosage: '',
        quantity: 0,
        periods: [],
        type: 'Comprimido',
        price: 0.0,
        requires_prescription: false,
        source: 'Comprado'
    });

    useEffect(() => {
        if (medicine) {
            setFormData(medicine);
        } else {
            // Reset for new medicine
            setFormData({
                id: crypto.randomUUID(),
                name: '',
                substance: '',
                dosage: '',
                quantity: 0,
                periods: [],
                type: 'Comprimido',
                price: 0.0,
                requires_prescription: false,
                source: 'Comprado'
            });
        }
    }, [medicine, isOpen]);

    if (!isOpen) return null;

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handlePeriodChange = (periodId) => {
        setFormData(prev => {
            const periods = prev.periods.includes(periodId)
                ? prev.periods.filter(p => p !== periodId)
                : [...prev.periods, periodId];
            return { ...prev, periods };
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave({
            ...formData,
            quantity: parseInt(formData.quantity) || 0,
            price: parseFloat(formData.price) || 0.0
        });
    };

    const PERIODS = [
        { id: 'cafe', label: 'Café da Manhã' },
        { id: 'almoco', label: 'Almoço' },
        { id: 'jantar', label: 'Jantar' },
        { id: 'dormir', label: 'Dormir' }
    ];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
            <Card className="w-full max-w-lg border-[rgb(var(--border))] bg-[rgb(var(--surface))] text-[rgb(var(--text))] max-h-[90vh] overflow-y-auto">
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="text-white">
                        {medicine ? 'Editar Medicamento' : 'Novo Medicamento'}
                    </CardTitle>
                    <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
                        <X className="h-4 w-4" />
                    </Button>
                </CardHeader>
                <form onSubmit={handleSubmit}>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Nome</label>
                            <input
                                required
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                className="w-full rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--background))] px-3 py-2 text-sm text-[rgb(var(--text))] focus:outline-none focus:ring-2 focus:ring-[rgb(var(--primary))]"
                                placeholder="Ex: AAS"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Dosagem</label>
                                <input
                                    required
                                    name="dosage"
                                    value={formData.dosage}
                                    onChange={handleChange}
                                    className="w-full rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--background))] px-3 py-2 text-sm text-[rgb(var(--text))]"
                                    placeholder="Ex: 100mg"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Quantidade</label>
                                <input
                                    required
                                    type="number"
                                    name="quantity"
                                    value={formData.quantity}
                                    onChange={handleChange}
                                    className="w-full rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--background))] px-3 py-2 text-sm text-[rgb(var(--text))]"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium">Princípio Ativo (Opcional)</label>
                            <input
                                name="substance"
                                value={formData.substance || ''}
                                onChange={handleChange}
                                className="w-full rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--background))] px-3 py-2 text-sm text-[rgb(var(--text))]"
                                placeholder="Ex: Ácido Acetilsalicílico"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Preço (R$)</label>
                                <input
                                    type="number"
                                    step="0.01"
                                    name="price"
                                    value={formData.price}
                                    onChange={handleChange}
                                    className="w-full rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--background))] px-3 py-2 text-sm text-[rgb(var(--text))]"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Fonte</label>
                                <select
                                    name="source"
                                    value={formData.source}
                                    onChange={handleChange}
                                    className="w-full rounded-md border border-[rgb(var(--border))] bg-[rgb(var(--background))] px-3 py-2 text-sm text-[rgb(var(--text))]"
                                >
                                    <option value="Comprado">Comprado</option>
                                    <option value="SUS">SUS</option>
                                </select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium block mb-2">Períodos</label>
                            <div className="grid grid-cols-2 gap-2">
                                {PERIODS.map(p => (
                                    <label key={p.id} className="flex items-center space-x-2 border border-[rgb(var(--border))] p-2 rounded cursor-pointer hover:bg-[rgb(var(--background))]">
                                        <input
                                            type="checkbox"
                                            checked={formData.periods.includes(p.id)}
                                            onChange={() => handlePeriodChange(p.id)}
                                            className="rounded border-[rgb(var(--border))] text-[rgb(var(--primary))]"
                                        />
                                        <span className="text-sm">{p.label}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                    </CardContent>
                    <CardFooter className="flex justify-end space-x-2">
                        <Button type="button" variant="ghost" onClick={onClose}>Cancelar</Button>
                        <Button type="submit">Salvar</Button>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}
