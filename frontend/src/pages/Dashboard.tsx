import { useState } from 'react';
import ChatWidget from '../components/ChatWidget';
import { User } from '../api';

interface DashboardProps {
  user: User;
  token: string;
  onLogout: () => void;
}

const formatCurrency = (value?: number) => {
  const amount = value ?? 0;
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
  }).format(amount);
};

export default function Dashboard({ user, token, onLogout }: DashboardProps) {

  const [sidebarOpen, setSidebarOpen] = useState(true);

  const menuItems = [
    { id: 'transfers', label: 'Transferencias', icon: '💸' },
    { id: 'payments', label: 'Pagos', icon: '💳' },
    { id: 'investments', label: 'Inversiones', icon: '📈' },
    { id: 'settings', label: 'Configuración', icon: '⚙️' },
  ];

  const transactions = [
    { id: 1, type: 'Cuenta creada', amount: user.balance ?? 0, date: 'Hoy', icon: '🏦' },
    { id: 2, type: 'Asistente conectado a PostgreSQL', amount: 0, date: 'Hoy', icon: '🤖' },
    { id: 3, type: 'Sesión segura iniciada', amount: 0, date: 'Hoy', icon: '🔐' },
  ];

  return (
    <div className="dashboard-container">

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

      <main className="dashboard-main">

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

        <div className="dashboard-content">

          <section className="balance-section">

            <div className="balance-card">

              <div className="balance-info">
                <p className="balance-label">Saldo disponible</p>
                <h2 className="balance-amount">{formatCurrency(user.balance)}</h2>
                <p className="balance-account">Cuenta de ahorro {user.accountNumber ? `· ${user.accountNumber}` : ''}</p>
              </div>

              <div className="balance-icon">$</div>

            </div>

            <div className="stats-cards">

              <div className="stat-card">
                <p className="stat-label">Cuenta vinculada</p>
                <p className="stat-value">{user.accountNumber || 'Pendiente'}</p>
                <p className="stat-detail">PostgreSQL</p>
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

          <section className="transactions-section">

            <h3>Últimas transacciones</h3>

            <p className="transactions-subtitle">
              Movimientos de referencia de la sesión actual
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
                    {formatCurrency(tx.amount)}
                  </p>

                </div>

              ))}

            </div>

          </section>

        </div>

      </main>

      <ChatWidget user={user} token={token} />

    </div>
  );
}
