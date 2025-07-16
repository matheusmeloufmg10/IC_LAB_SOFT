// Configuração da API
const API_BASE_URL = 'http://localhost:8000/api';

// Função para fazer upload de arquivos
export const uploadFiles = async (files) => {
  try {
    const formData = new FormData();
    
    // Adicionar cada arquivo ao FormData
    files.forEach((file, index) => {
      formData.append('file', file);
    });

    const response = await fetch(`${API_BASE_URL}/upload/`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error('Erro no upload:', error);
    return { success: false, error: error.message };
  }
};

// Função para obter histórico de uploads
export const getUploadHistory = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/uploads/`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error('Erro ao buscar histórico:', error);
    return { success: false, error: error.message };
  }
};

// Função para obter detalhes de um upload específico
export const getUploadDetails = async (uploadId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/uploads/${uploadId}/`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error('Erro ao buscar detalhes:', error);
    return { success: false, error: error.message };
  }
};

// Função para validar arquivo antes do upload
export const validateFile = (file) => {
  const maxSize = 200 * 1024 * 1024; // 200MB
  const allowedTypes = ['.zip', '.rar'];
  
  // Verificar tamanho
  if (file.size > maxSize) {
    return { valid: false, error: 'Arquivo muito grande. Máximo 200MB.' };
  }
  
  // Verificar tipo
  const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
  if (!allowedTypes.includes(fileExtension)) {
    return { valid: false, error: 'Tipo de arquivo não suportado. Use ZIP ou RAR.' };
  }
  
  return { valid: true };
};

// Função para formatar resposta da API
export const formatApiResponse = (response) => {
  if (response.success) {
    return {
      status: 'success',
      message: 'Upload realizado com sucesso!',
      data: response.data
    };
  } else {
    return {
      status: 'error',
      message: response.error || 'Erro desconhecido',
      data: null
    };
  }
}; 