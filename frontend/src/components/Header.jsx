import React from 'react';
import { NavLink } from 'react-router-dom';

const Header = () => {
  return (
    <header className="fixed top-0 left-0 right-0 bg-white/80 backdrop-blur-sm border-b border-primary-200 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Nome do Sistema */}
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-accent-500 to-accent-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h1 className="text-xl font-semibold text-primary-900">IC Lab Soft</h1>
          </div>
          
          {/* Menu/Navegação */}
          <nav className="hidden md:flex items-center space-x-8">
            <NavLink to="/" className={({isActive}) => isActive ? "text-accent-600 font-bold" : "text-primary-600 hover:text-accent-600 transition-colors duration-200 font-medium"} end>
              Upload
            </NavLink>
            <NavLink to="/dashboard" className={({isActive}) => isActive ? "text-accent-600 font-bold" : "text-primary-500 hover:text-accent-600 transition-colors duration-200"}>
              Dashboard
            </NavLink>
            <a href="#" className="text-primary-500 hover:text-accent-600 transition-colors duration-200">
              Histórico
            </a>
            <a href="#" className="text-primary-500 hover:text-accent-600 transition-colors duration-200">
              Configurações
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header; 