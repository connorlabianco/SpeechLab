import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import '../../styles/components/layout/Header.css';

function Header() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">
          <span className="logo-icon">🗣️</span>
          <span className="logo-text">SpeechLabs</span>
        </Link>
        <nav className="main-nav">
          {isAuthenticated ? (
            <div className="user-menu">
              {user && (
                <div className="user-info">
                  {user.picture && (
                    <img 
                      src={user.picture} 
                      alt={user.name || 'User'} 
                      className="user-avatar"
                    />
                  )}
                  <span className="user-name">{user.name || user.email}</span>
                </div>
              )}
              <button 
                className="btn-logout"
                onClick={handleLogout}
                type="button"
              >
                Logout
              </button>
            </div>
          ) : (
            <ul>
              <li><Link to="/login">Login</Link></li>
              <li><a href="https://github.com/yourusername/speechlabs" target="_blank" rel="noopener noreferrer">GitHub</a></li>
            </ul>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;
