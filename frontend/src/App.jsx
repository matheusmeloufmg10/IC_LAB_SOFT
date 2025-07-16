import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import Header from './components/Header';
import FileUpload from './components/FileUpload';
import UploadStatus from './components/UploadStatus';
import Dashboard from './components/Dashboard';

function App() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Handler para arquivos selecionados
  const handleFilesSelected = (files) => {
    setSelectedFiles(files);
    setUploadStatus(null); // Limpar status anterior
    console.log('Arquivos selecionados:', files);
  };

  // Handler para upload (simulado)
  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatus({ status: 'uploading', message: 'Iniciando processamento...' });
    
    try {
      // Simular progresso de upload
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setUploadProgress(i);
        
        if (i === 30) {
          setUploadStatus({ status: 'uploading', message: 'Extraindo arquivos...' });
        } else if (i === 60) {
          setUploadStatus({ status: 'uploading', message: 'Processando PDFs e DXFs...' });
        } else if (i === 90) {
          setUploadStatus({ status: 'uploading', message: 'Salvando no banco de dados...' });
        }
      }
      
      // Simular conclusão
      await new Promise(resolve => setTimeout(resolve, 500));
      setUploadStatus({ 
        status: 'success', 
        message: `Processamento concluído! ${selectedFiles.length} arquivo(s) processado(s) com sucesso.` 
      });
      
      console.log('Upload simulado concluído!');
      // Aqui você pode integrar com o backend real
      // const formData = new FormData();
      // selectedFiles.forEach(file => formData.append('file', file));
      // const response = await fetch('/api/upload/', { method: 'POST', body: formData });
      
    } catch (error) {
      console.error('Erro no upload:', error);
      setUploadStatus({ 
        status: 'error', 
        message: 'Erro durante o processamento. Tente novamente.' 
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100">
      {/* Header fixo */}
      <Header />
      
      {/* Conteúdo principal com rotas */}
      <main className="pt-20 pb-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={
              <>
                {/* Seção de introdução */}
                <div className="text-center mb-12 animate-fade-in">
                  <h2 className="text-3xl sm:text-4xl font-bold text-primary-900 mb-4">
                    Processamento de Arquivos Técnicos
                  </h2>
                  <p className="text-lg text-primary-600 max-w-2xl mx-auto">
                    Faça upload de seus arquivos ZIP ou RAR contendo PDFs e DXFs para processamento automático 
                    e extração de informações técnicas.
                  </p>
                </div>

                {/* Componente de Upload */}
                <div className="mb-8">
                  <FileUpload
                    onFilesSelected={handleFilesSelected}
                    acceptedTypes=".zip,.rar"
                    maxFiles={5}
                  />
                </div>

                {/* Status do Upload */}
                {uploadStatus && (
                  <div className="mb-8">
                    <UploadStatus 
                      status={uploadStatus.status}
                      message={uploadStatus.message}
                      progress={uploadProgress}
                    />
                  </div>
                )}

                {/* Botão de Upload */}
                {selectedFiles.length > 0 && !isUploading && (
                  <div className="text-center animate-slide-up">
                    <button
                      onClick={handleUpload}
                      disabled={isUploading}
                      className="btn-primary"
                    >
                      Processar {selectedFiles.length} arquivo{selectedFiles.length > 1 ? 's' : ''}
                    </button>
                  </div>
                )}

                {/* Informações adicionais */}
                <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 animate-fade-in">
                  <div className="text-center p-6 bg-white rounded-xl border border-primary-200 hover:shadow-lg transition-shadow duration-200">
                    <div className="w-12 h-12 bg-accent-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                      <svg className="w-6 h-6 text-accent-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-primary-900 mb-2">Processamento Rápido</h3>
                    <p className="text-primary-600 text-sm">
                      Extração automática de dados técnicos de PDFs e DXFs em segundos.
                    </p>
                  </div>

                  <div className="text-center p-6 bg-white rounded-xl border border-primary-200 hover:shadow-lg transition-shadow duration-200">
                    <div className="w-12 h-12 bg-accent-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                      <svg className="w-6 h-6 text-accent-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-primary-900 mb-2">Validação Inteligente</h3>
                    <p className="text-primary-600 text-sm">
                      Verificação automática de dados e estrutura dos arquivos enviados.
                    </p>
                  </div>

                  <div className="text-center p-6 bg-white rounded-xl border border-primary-200 hover:shadow-lg transition-shadow duration-200">
                    <div className="w-12 h-12 bg-accent-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                      <svg className="w-6 h-6 text-accent-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-primary-900 mb-2">Armazenamento Seguro</h3>
                    <p className="text-primary-600 text-sm">
                      Dados processados são salvos de forma estruturada no banco de dados.
                    </p>
                  </div>
                </div>
              </>
            } />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default App; 