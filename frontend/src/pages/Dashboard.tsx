import React, { useState } from 'react';
import ChatWidget from '../components/ChatWidget';

interface User {
  id: string;
  name: string;
  email: string;
}

interface DashboardProps {
  user: User;
  onLogout: () => void;
}

export default function Dashboard({ user, onLogout }: DashboardProps) {

  const [sidebarOpen, setSidebarOpen] = useState(true);

  const menuItems = [
    { id: 'transfers', label: 'Transferencias', icon: '💸' },
    { id: 'payments', label: 'Pagos', icon: '💳' },
    { id: 'investments', label: 'Inversiones', icon: '📈' },
    { id: 'settings', label: 'Configuración', icon: '⚙️' },
  ];

  const transactions = [
    { id: 1, type: 'Compra en Supermercado', amount: -450.00, date: 'Hoy', icon: '🛒' },
    { id: 2, type: 'Transferencia recibida', amount: 2000.00, date: 'Ayer', icon: '👤' },
    { id: 3, type: 'Pago de servicios', amount: -350.00, date: '2 días atrás', icon: '💡' },
  ];

  return (
    <div className="dashboard-container">

      {/* SIDEBAR */}

      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>

        <div className="sidebar-header">
          <div className="logo">B</div>
          {sidebarOpen && <h2>Banco Digital</h2>}
        </div>

        <nav className="sidebar-menu">

          {menuItems.map(item => (
            <a
              key={item.id}
              href="#"
              className="menu-item"
              title={item.label}
            >
              <span className="menu-icon">{item.icon}</span>

              {sidebarOpen && (
                <span className="menu-label">
                  {item.label}
                </span>
              )}
            </a>
          ))}

        </nav>

        <div className="sidebar-footer">
          <button
            onClick={onLogout}
            className="logout-button"
          >
            {sidebarOpen ? '🚪 Cerrar sesión' : '🚪'}
          </button>
        </div>

      </aside>


      {/* MAIN */}

      <main className="dashboard-main">

        {/* HEADER */}

        <header className="dashboard-header">

          <button
            className="toggle-sidebar-btn"
            onClick={() => setSidebarOpen(prev => !prev)}
          >
            ☰
          </button>

          <h1>Inicio</h1>

          <div className="user-info">

            <div className="user-avatar">
              {user.name.charAt(0).toUpperCase()}
            </div>

            <div className="user-details">
              <p className="user-name">{user.name}</p>
              <p className="user-email">{user.email}</p>
            </div>

          </div>

        </header>


        {/* CONTENT */}

        <div className="dashboard-content">

          {/* BALANCE */}

          <section className="balance-section">

            <div className="balance-card">

              <div className="balance-info">
                <p className="balance-label">Saldo disponible</p>
                <h2 className="balance-amount">$15,234.50</h2>
                <p className="balance-account">Cuenta de ahorro</p>
              </div>

              <div className="balance-icon">$</div>

            </div>


            <div className="stats-cards">

              <div className="stat-card">
                <p className="stat-label">Movimientos recientes</p>
                <p className="stat-value">3</p>
                <p className="stat-detail">Últimos 7 días</p>
              </div>

              <div className="stat-card">
                <p className="stat-label">Tasa de ahorro</p>
                <p className="stat-value">3.5%</p>
                <p className="stat-detail">Anual</p>
              </div>

              <div className="stat-card">
                <p className="stat-label">Límite disponible</p>
                <p className="stat-value">$5,000</p>
                <p className="stat-detail">Crédito</p>
              </div>

            </div>

          </section>


          {/* ACCIONES RAPIDAS */}

          <section className="quick-actions-section">

            <h3>Acciones rápidas</h3>

            <div className="quick-actions">

              <button className="action-btn action-transfer">
                <span className="action-icon">↗️</span>
                <span className="action-label">Transferir</span>
              </button>

              <button className="action-btn action-receive">
                <span className="action-icon">↙️</span>
                <span className="action-label">Recibir</span>
              </button>

              <button className="action-btn action-pay">
                <span className="action-icon">📤</span>
                <span className="action-label">Pagar</span>
              </button>

              <button className="action-btn action-invest">
                <span className="action-icon">📈</span>
                <span className="action-label">Invertir</span>
              </button>

            </div>

          </section>


          {/* TRANSACCIONES */}

          <section className="transactions-section">

            <h3>Últimas transacciones</h3>

            <p className="transactions-subtitle">
              Movimientos de los últimos 30 días
            </p>

            <div className="transactions-list">

              {transactions.map(tx => (

                <div
                  key={tx.id}
                  className="transaction-item"
                >

                  <div className="transaction-left">

                    <div className="transaction-icon">
                      {tx.icon}
                    </div>

                    <div className="transaction-info">
                      <p className="transaction-type">{tx.type}</p>
                      <p className="transaction-date">{tx.date}</p>
                    </div>

                  </div>

                  <p
                    className={`transaction-amount ${tx.amount > 0 ? 'positive' : 'negative'}`}
                  >
                    {tx.amount > 0 ? '+' : ''}
                    {tx.amount.toFixed(2)}
                  </p>

                </div>

              ))}

            </div>

          </section>

        </div>

      </main>

      <ChatWidget />

    </div>
  );
}