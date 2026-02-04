'use client';

import { NeoSidebar as Sidebar } from '../../components/design-system/NeoSidebar';
import { Settings, Wrench, Lock, Bell, Server } from 'lucide-react';

export default function SettingsPage() {
    return (
        <div className="flex bg-[#050505] h-screen overflow-hidden font-sans text-gray-100">
            <Sidebar />

            <main className="flex-1 overflow-y-auto relative h-full flex flex-col items-center justify-center p-8">
                {/* Ambient Background */}
                <div className="fixed inset-0 pointer-events-none z-0">
                    <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] bg-synapse-purple/5 blur-[100px] rounded-full" />
                    <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-blue-500/5 blur-[100px] rounded-full" />
                </div>

                <div className="relative z-10 max-w-2xl w-full text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">

                    {/* Icon Container */}
                    <div className="mx-auto w-24 h-24 rounded-3xl bg-gradient-to-br from-white/5 to-transparent border border-white/10 flex items-center justify-center shadow-[0_0_30px_rgba(139,92,246,0.1)] mb-6 group">
                        <Settings className="w-10 h-10 text-synapse-purple group-hover:rotate-90 transition-transform duration-700 ease-in-out" />
                    </div>

                    <div className="space-y-4">
                        <h1 className="text-4xl font-extrabold tracking-tight">
                            <span className="bg-clip-text text-transparent bg-gradient-to-r from-white via-gray-200 to-gray-500">
                                Configurações Globais
                            </span>
                        </h1>
                        <p className="text-gray-400 text-lg max-w-lg mx-auto leading-relaxed">
                            Estamos construindo um painel centralizado para você gerenciar todo o ecossistema Synapse.
                        </p>
                    </div>

                    {/* Features Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left mt-12">
                        <FeatureCard
                            icon={Lock}
                            title="Chaves de API"
                            desc="Gerencie chaves da OpenAI, TikTok e ElevenLabs em um só lugar."
                        />
                        <FeatureCard
                            icon={Wrench}
                            title="Padrões do Sistema"
                            desc="Defina intervalos globais, horários de pico e limites de upload."
                        />
                        <FeatureCard
                            icon={Bell}
                            title="Notificações"
                            desc="Integração com Telegram/Discord para alertas em tempo real."
                        />
                        <FeatureCard
                            icon={Server}
                            title="Diagnóstico"
                            desc="Ferramentas avançadas de limpeza de cache e logs."
                        />
                    </div>

                    <div className="pt-8">
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/5 text-sm text-gray-500">
                            <span className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
                            Em desenvolvimento - Chega na próxima atualização
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

function FeatureCard({ icon: Icon, title, desc }: { icon: any, title: string, desc: string }) {
    return (
        <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.05] transition-colors group">
            <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-white/5 group-hover:text-synapse-purple transition-colors">
                    <Icon className="w-5 h-5" />
                </div>
                <div>
                    <h3 className="font-bold text-white text-sm">{title}</h3>
                    <p className="text-xs text-gray-500 mt-1 leading-relaxed">{desc}</p>
                </div>
            </div>
        </div>
    );
}
