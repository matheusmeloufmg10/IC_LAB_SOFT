import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const API_BASE = '/api/dashboard'; // Ajuste conforme proxy/backend

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(null);
  const [pecas, setPecas] = useState([]);
  const [paginacao, setPaginacao] = useState({ pagina_atual: 1, tamanho_pagina: 10, total_pecas: 0, total_paginas: 1 });
  const [busca, setBusca] = useState('');
  const [loadingPecas, setLoadingPecas] = useState(false);
  const [detalhePeca, setDetalhePeca] = useState(null);
  const [loadingDetalhe, setLoadingDetalhe] = useState(false);

  // Polling para estatísticas gerais
  useEffect(() => {
    let interval;
    async function fetchStats() {
      setLoading(true);
      try {
        const resp = await fetch(`${API_BASE}/stats/`);
        if (!resp.ok) throw new Error('Erro ao buscar estatísticas');
        const data = await resp.json();
        setStats(data);
      } catch (e) {
        setErro(e.message);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
    interval = setInterval(fetchStats, 10000); // 10 segundos
    return () => clearInterval(interval);
  }, []);

  // Buscar peças paginadas
  useEffect(() => {
    async function fetchPecas() {
      setLoadingPecas(true);
      try {
        const params = new URLSearchParams({
          page: paginacao.pagina_atual,
          page_size: paginacao.tamanho_pagina,
          search: busca
        });
        const resp = await fetch(`${API_BASE}/pecas/?${params.toString()}`);
        if (!resp.ok) throw new Error('Erro ao buscar peças');
        const data = await resp.json();
        setPecas(data.pecas);
        setPaginacao(data.paginacao);
      } catch (e) {
        setErro(e.message);
      } finally {
        setLoadingPecas(false);
      }
    }
    fetchPecas();
  }, [paginacao.pagina_atual, paginacao.tamanho_pagina, busca]);

  // Buscar detalhes da peça
  async function abrirDetalhePeca(codigo) {
    setLoadingDetalhe(true);
    try {
      const resp = await fetch(`${API_BASE}/pecas/${codigo}/`);
      if (!resp.ok) throw new Error('Erro ao buscar detalhes da peça');
      const data = await resp.json();
      setDetalhePeca(data);
    } catch (e) {
      setErro(e.message);
    } finally {
      setLoadingDetalhe(false);
    }
  }

  if (loading) return <div className="text-center py-16 text-primary-600">Carregando dashboard...</div>;
  if (erro) return <div className="text-center py-16 text-red-600">{erro}</div>;
  if (!stats) return null;

  return (
    <div className="animate-fade-in">
      <h2 className="text-2xl sm:text-3xl font-bold text-primary-900 mb-8 text-center">Dashboard de Peças</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        <Card title="Total de Peças" value={stats.estatisticas_gerais.total_pecas_principais} />
        <Card title="Total de Subpeças" value={stats.estatisticas_gerais.total_subpecas} />
        <Card title="Peças nos últimos 7 dias" value={stats.estatisticas_gerais.pecas_recentes_7dias} />
        <Card title="Perímetro Médio (mm)" value={stats.estatisticas_gerais.perimetro_medio_mm} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
        <div className="bg-white rounded-xl p-6 border border-primary-200">
          <h3 className="font-semibold text-primary-800 mb-4">Peças por Material</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={stats.materiais} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="material" fontSize={12} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="quantidade" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-xl p-6 border border-primary-200">
          <h3 className="font-semibold text-primary-800 mb-4">Peças por Espessura</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={stats.espessuras} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="espessura" fontSize={12} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="quantidade" fill="#059669" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 border border-primary-200 mb-10">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-2">
          <h3 className="font-semibold text-primary-800">Peças Cadastradas</h3>
          <input
            type="text"
            placeholder="Buscar por código..."
            className="input input-bordered w-full sm:w-64"
            value={busca}
            onChange={e => { setBusca(e.target.value); setPaginacao(p => ({...p, pagina_atual: 1})); }}
          />
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-primary-700 border-b">
                <th className="py-2 pr-4">Código</th>
                <th className="py-2 pr-4">Data</th>
                <th className="py-2 pr-4">Subpeças</th>
                <th className="py-2 pr-4">Materiais</th>
                <th className="py-2 pr-4">Espessuras</th>
                <th className="py-2 pr-4">Perímetro Total</th>
                <th className="py-2 pr-4">Tempo Corte Total</th>
              </tr>
            </thead>
            <tbody>
              {loadingPecas ? (
                <tr><td colSpan={7} className="text-center py-4">Carregando...</td></tr>
              ) : pecas.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-4">Nenhuma peça encontrada.</td></tr>
              ) : pecas.map((peca) => (
                <tr key={peca.codigo} className="border-b hover:bg-primary-50 cursor-pointer" onClick={() => abrirDetalhePeca(peca.codigo)}>
                  <td className="py-2 pr-4 font-mono">{peca.codigo}</td>
                  <td className="py-2 pr-4">{peca.created_at ? new Date(peca.created_at).toLocaleDateString() : '-'}</td>
                  <td className="py-2 pr-4">{peca.total_subpecas}</td>
                  <td className="py-2 pr-4">{peca.materiais_unicos}</td>
                  <td className="py-2 pr-4">{peca.espessuras_unicas}</td>
                  <td className="py-2 pr-4">{peca.perimetro_total.toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
                  <td className="py-2 pr-4">{peca.tempo_corte_total.toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {/* Paginação */}
        <div className="flex justify-center items-center gap-2 mt-4 flex-wrap">
          <button
            className="btn btn-sm"
            disabled={paginacao.pagina_atual === 1}
            onClick={() => setPaginacao(p => ({...p, pagina_atual: p.pagina_atual - 1}))}
          >Anterior</button>
          <span className="text-primary-700 text-sm">Página {paginacao.pagina_atual} de {paginacao.total_paginas}</span>
          <button
            className="btn btn-sm"
            disabled={paginacao.pagina_atual === paginacao.total_paginas}
            onClick={() => setPaginacao(p => ({...p, pagina_atual: p.pagina_atual + 1}))}
          >Próxima</button>
        </div>
      </div>

      {/* Modal de detalhes da peça */}
      {detalhePeca && (
        <ModalDetalhePeca
          detalhe={detalhePeca}
          loading={loadingDetalhe}
          onClose={() => setDetalhePeca(null)}
        />
      )}
    </div>
  );
}

function Card({ title, value }) {
  return (
    <div className="bg-white rounded-xl p-6 border border-primary-200 text-center shadow-sm">
      <div className="text-2xl font-bold text-primary-900 mb-1">{value}</div>
      <div className="text-primary-600 text-sm">{title}</div>
    </div>
  );
}

function ModalDetalhePeca({ detalhe, loading, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-lg max-w-2xl w-full p-6 relative animate-fade-in">
        <button className="absolute top-2 right-2 text-primary-500 hover:text-red-500" onClick={onClose}>&times;</button>
        <h3 className="text-xl font-bold mb-2 text-primary-900">Detalhes da Peça: <span className="font-mono">{detalhe.peca.codigo}</span></h3>
        <div className="mb-4 text-primary-700 text-sm">Cadastrada em: {detalhe.peca.created_at ? new Date(detalhe.peca.created_at).toLocaleString() : '-'}</div>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div><b>Total de Subpeças:</b> {detalhe.estatisticas.total_subpecas}</div>
          <div><b>Materiais únicos:</b> {detalhe.estatisticas.materiais_unicos}</div>
          <div><b>Espessuras únicas:</b> {detalhe.estatisticas.espessuras_unicas}</div>
          <div><b>Perímetro total:</b> {detalhe.estatisticas.perimetro_total.toLocaleString(undefined, {maximumFractionDigits: 2})}</div>
          <div><b>Tempo corte total:</b> {detalhe.estatisticas.tempo_corte_total.toLocaleString(undefined, {maximumFractionDigits: 2})}</div>
          <div><b>Perímetro médio:</b> {detalhe.estatisticas.perimetro_medio.toLocaleString(undefined, {maximumFractionDigits: 2})}</div>
          <div><b>Tempo corte médio:</b> {detalhe.estatisticas.tempo_corte_medio.toLocaleString(undefined, {maximumFractionDigits: 2})}</div>
        </div>
        <div className="overflow-x-auto max-h-64">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="text-left text-primary-700 border-b">
                <th className="py-1 pr-2">Código</th>
                <th className="py-1 pr-2">Nome</th>
                <th className="py-1 pr-2">Material</th>
                <th className="py-1 pr-2">Espessura</th>
                <th className="py-1 pr-2">Perímetro</th>
                <th className="py-1 pr-2">Tempo Corte</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="text-center py-2">Carregando...</td></tr>
              ) : detalhe.subpecas.length === 0 ? (
                <tr><td colSpan={6} className="text-center py-2">Nenhuma subpeça encontrada.</td></tr>
              ) : detalhe.subpecas.map((sp) => (
                <tr key={sp.codigo} className="border-b">
                  <td className="py-1 pr-2 font-mono">{sp.codigo}</td>
                  <td className="py-1 pr-2">{sp.nome}</td>
                  <td className="py-1 pr-2">{sp.material}</td>
                  <td className="py-1 pr-2">{sp.espessura}</td>
                  <td className="py-1 pr-2">{sp.perimetro_mm.toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
                  <td className="py-1 pr-2">{sp.tempo_corte_segundos.toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Dashboard; 