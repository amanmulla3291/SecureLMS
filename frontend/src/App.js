import React, { useState, useEffect } from 'react';
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { 
  PlusIcon, 
  HomeIcon, 
  BookOpenIcon, 
  UserGroupIcon, 
  CogIcon,
  SunIcon,
  MoonIcon,
  Bars3Icon,
  XMarkIcon,
  AcademicCapIcon,
  ChartBarIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';
import './App.css';

// Auth0 configuration
const AUTH0_DOMAIN = "buildbytes.ca.auth0.com";
const AUTH0_CLIENT_ID = "zzgtGuezK2uzC4ONnqjjSN6F5LBaJgi1";
const AUTH0_AUDIENCE = "https://buildbytes-api.com";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Theme Context
const ThemeContext = React.createContext();

// Theme Provider
function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem('buildbytes-theme');
    return savedTheme || 'light';
  });

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('buildbytes-theme', newTheme);
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

// Loading component
function Loading() {
  return (
    <div className="loading-container">
      <div className="loading-spinner"></div>
      <p>Loading BuildBytes LMS...</p>
    </div>
  );
}

// Login component
function LoginButton() {
  const { loginWithRedirect } = useAuth0();

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <AcademicCapIcon className="login-icon" />
          <h1>BuildBytes LMS</h1>
          <p>Learning Management System for Technical Projects</p>
        </div>
        <button 
          onClick={() => loginWithRedirect()} 
          className="login-button"
        >
          Login to Continue
        </button>
      </div>
    </div>
  );
}

// Main Dashboard Layout
function DashboardLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const { logout, getAccessTokenSilently } = useAuth0();
  const { theme, toggleTheme } = React.useContext(ThemeContext);

  // Fetch current user info
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const token = await getAccessTokenSilently();
        const response = await axios.get(`${API}/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setCurrentUser(response.data);
      } catch (error) {
        console.error('Error fetching user:', error);
      }
    };
    fetchUser();
  }, [getAccessTokenSilently]);

  const navigation = currentUser?.role === 'mentor' 
    ? [
        { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
        { name: 'Subject Categories', href: '/subjects', icon: BookOpenIcon },
        { name: 'Projects', href: '/projects', icon: ChartBarIcon },
        { name: 'Students', href: '/students', icon: UserGroupIcon },
        { name: 'Settings', href: '/settings', icon: CogIcon },
      ]
    : [
        { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
        { name: 'My Projects', href: '/projects', icon: ChartBarIcon },
        { name: 'Resources', href: '/resources', icon: BookOpenIcon },
        { name: 'Settings', href: '/settings', icon: CogIcon },
      ];

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <AcademicCapIcon className="sidebar-logo-icon" />
            <span>BuildBytes LMS</span>
          </div>
          <button 
            className="sidebar-close"
            onClick={() => setSidebarOpen(false)}
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>
        
        <nav className="sidebar-nav">
          {navigation.map((item) => (
            <a key={item.name} href={item.href} className="sidebar-nav-item">
              <item.icon className="sidebar-nav-icon" />
              {item.name}
            </a>
          ))}
        </nav>
        
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-user-info">
              <p className="sidebar-user-name">{currentUser?.name}</p>
              <p className="sidebar-user-role">{currentUser?.role}</p>
            </div>
          </div>
          <button 
            onClick={() => logout({ returnTo: window.location.origin })}
            className="sidebar-logout"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {/* Header */}
        <header className="header">
          <button 
            className="mobile-menu-button"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <Bars3Icon className="w-6 h-6" />
          </button>
          
          <div className="header-actions">
            <button 
              onClick={toggleTheme}
              className="theme-toggle"
            >
              {theme === 'light' ? <MoonIcon className="w-5 h-5" /> : <SunIcon className="w-5 h-5" />}
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="page-content">
          {children}
        </main>
      </div>
    </div>
  );
}

// Dashboard Stats Component
function DashboardStats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { getAccessTokenSilently } = useAuth0();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = await getAccessTokenSilently();
        const response = await axios.get(`${API}/dashboard/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [getAccessTokenSilently]);

  if (loading) return <Loading />;

  return (
    <div className="dashboard-stats">
      <h1 className="page-title">Dashboard</h1>
      
      <div className="stats-grid">
        {stats?.user_role === 'mentor' ? (
          <>
            <div className="stat-card">
              <div className="stat-icon">
                <BookOpenIcon className="w-8 h-8" />
              </div>
              <div className="stat-content">
                <h3>Subject Categories</h3>
                <p className="stat-number">{stats.total_categories}</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">
                <ChartBarIcon className="w-8 h-8" />
              </div>
              <div className="stat-content">
                <h3>Total Projects</h3>
                <p className="stat-number">{stats.total_projects}</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">
                <UserGroupIcon className="w-8 h-8" />
              </div>
              <div className="stat-content">
                <h3>Students</h3>
                <p className="stat-number">{stats.total_students}</p>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="stat-card">
              <div className="stat-icon">
                <ChartBarIcon className="w-8 h-8" />
              </div>
              <div className="stat-content">
                <h3>Assigned Projects</h3>
                <p className="stat-number">{stats.assigned_projects}</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">
                <AcademicCapIcon className="w-8 h-8" />
              </div>
              <div className="stat-content">
                <h3>Completed Tasks</h3>
                <p className="stat-number">{stats.completed_tasks}</p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// Subject Categories Component
function SubjectCategories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const { getAccessTokenSilently } = useAuth0();

  const fetchCategories = async () => {
    try {
      const token = await getAccessTokenSilently();
      const response = await axios.get(`${API}/subject-categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, [getAccessTokenSilently]);

  const handleCreateCategory = async (categoryData) => {
    try {
      const token = await getAccessTokenSilently();
      await axios.post(`${API}/subject-categories`, categoryData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowCreateModal(false);
      fetchCategories();
    } catch (error) {
      console.error('Error creating category:', error);
    }
  };

  const handleUpdateCategory = async (categoryId, categoryData) => {
    try {
      const token = await getAccessTokenSilently();
      await axios.put(`${API}/subject-categories/${categoryId}`, categoryData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEditingCategory(null);
      fetchCategories();
    } catch (error) {
      console.error('Error updating category:', error);
    }
  };

  const handleDeleteCategory = async (categoryId) => {
    if (window.confirm('Are you sure you want to delete this category?')) {
      try {
        const token = await getAccessTokenSilently();
        await axios.delete(`${API}/subject-categories/${categoryId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        fetchCategories();
      } catch (error) {
        console.error('Error deleting category:', error);
      }
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="subject-categories">
      <div className="page-header">
        <h1 className="page-title">Subject Categories</h1>
        <button 
          className="btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          <PlusIcon className="w-5 h-5" />
          Add Category
        </button>
      </div>

      <div className="categories-grid">
        {categories.map((category) => (
          <div key={category.id} className="category-card">
            <div className="category-header">
              <div 
                className="category-color"
                style={{ backgroundColor: category.color }}
              ></div>
              <h3>{category.name}</h3>
              <div className="category-actions">
                <button 
                  onClick={() => setEditingCategory(category)}
                  className="btn-icon"
                >
                  <PencilIcon className="w-4 h-4" />
                </button>
                <button 
                  onClick={() => handleDeleteCategory(category.id)}
                  className="btn-icon btn-danger"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
            <p className="category-description">{category.description}</p>
            <div className="category-meta">
              <span className="category-date">
                Created {new Date(category.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Create Category Modal */}
      {showCreateModal && (
        <CategoryModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateCategory}
        />
      )}

      {/* Edit Category Modal */}
      {editingCategory && (
        <CategoryModal
          category={editingCategory}
          onClose={() => setEditingCategory(null)}
          onSubmit={(data) => handleUpdateCategory(editingCategory.id, data)}
        />
      )}
    </div>
  );
}

// Category Modal Component
function CategoryModal({ category, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    name: category?.name || '',
    description: category?.description || '',
    color: category?.color || '#3B82F6'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h2>{category ? 'Edit Category' : 'Create Category'}</h2>
          <button onClick={onClose} className="modal-close">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>Category Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              rows="3"
              required
            />
          </div>
          
          <div className="form-group">
            <label>Color</label>
            <input
              type="color"
              value={formData.color}
              onChange={(e) => setFormData({...formData, color: e.target.value})}
            />
          </div>
          
          <div className="form-actions">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              {category ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Main App Component
function AppContent() {
  const { isLoading, isAuthenticated } = useAuth0();

  if (isLoading) return <Loading />;

  if (!isAuthenticated) {
    return <LoginButton />;
  }

  return (
    <Router>
      <DashboardLayout>
        <Routes>
          <Route path="/dashboard" element={<DashboardStats />} />
          <Route path="/subjects" element={<SubjectCategories />} />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </DashboardLayout>
    </Router>
  );
}

function App() {
  return (
    <Auth0Provider
      domain={AUTH0_DOMAIN}
      clientId={AUTH0_CLIENT_ID}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: AUTH0_AUDIENCE,
      }}
    >
      <ThemeProvider>
        <div className="App">
          <AppContent />
        </div>
      </ThemeProvider>
    </Auth0Provider>
  );
}

export default App;