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

// Landing Page Component
function LandingPage() {
  const { loginWithRedirect } = useAuth0();
  
  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-background">
          <img 
            src="https://images.unsplash.com/photo-1530825894095-9c184b068fcb?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHwyfHxsZWFybmluZ3xlbnwwfHx8Ymx1ZXwxNzUyMzk2NTEzfDA&ixlib=rb-4.1.0&q=85"
            alt="Modern Learning Technology"
            className="hero-image"
          />
          <div className="hero-overlay"></div>
        </div>
        
        <div className="hero-content">
          <div className="hero-text">
            <div className="hero-badge">
              <AcademicCapIcon className="hero-badge-icon" />
              <span>BuildBytes LMS</span>
            </div>
            <h1 className="hero-title">
              Transform Your Learning Experience
            </h1>
            <p className="hero-subtitle">
              A modern Learning Management System designed for technical projects, 
              collaborative learning, and professional development.
            </p>
            <div className="hero-features">
              <div className="feature-item">
                <BookOpenIcon className="feature-icon" />
                <span>Interactive Projects</span>
              </div>
              <div className="feature-item">
                <UserGroupIcon className="feature-icon" />
                <span>Collaborative Learning</span>
              </div>
              <div className="feature-item">
                <ChartBarIcon className="feature-icon" />
                <span>Progress Tracking</span>
              </div>
            </div>
          </div>
          
          <div className="hero-auth">
            <div className="auth-card">
              <h2>Get Started Today</h2>
              <p>Join thousands of learners and mentors</p>
              
              <div className="auth-buttons">
                <button 
                  onClick={() => loginWithRedirect({ screen_hint: 'signup' })}
                  className="auth-button auth-button-primary"
                >
                  Create Account
                </button>
                <button 
                  onClick={() => loginWithRedirect()}
                  className="auth-button auth-button-secondary"
                >
                  Sign In
                </button>
              </div>
              
              <div className="auth-divider">
                <span>or</span>
              </div>
              
              <div className="demo-info">
                <p className="demo-text">
                  Want to explore first? 
                  <button 
                    onClick={() => loginWithRedirect()}
                    className="demo-link"
                  >
                    Try Demo
                  </button>
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="container">
          <div className="features-header">
            <h2>Why Choose BuildBytes LMS?</h2>
            <p>Everything you need to manage learning and projects effectively</p>
          </div>
          
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-card-icon">
                <BookOpenIcon className="w-8 h-8" />
              </div>
              <h3>Subject Categories</h3>
              <p>Organize learning materials into structured categories for easy navigation and management.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-card-icon">
                <ChartBarIcon className="w-8 h-8" />
              </div>
              <h3>Project Management</h3>
              <p>Create, assign, and track projects with detailed task management and progress monitoring.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-card-icon">
                <UserGroupIcon className="w-8 h-8" />
              </div>
              <h3>Role-Based Access</h3>
              <p>Separate interfaces for mentors and students with appropriate permissions and features.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-card-icon">
                <AcademicCapIcon className="w-8 h-8" />
              </div>
              <h3>Task Tracking</h3>
              <p>Monitor assignment progress with status updates, submissions, and feedback systems.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-card-icon">
                <CogIcon className="w-8 h-8" />
              </div>
              <h3>Customizable</h3>
              <p>Personalize your learning environment with themes, settings, and custom configurations.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-card-icon">
                <HomeIcon className="w-8 h-8" />
              </div>
              <h3>Analytics Dashboard</h3>
              <p>Comprehensive insights into learning progress, project completion, and performance metrics.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Ready to Start Learning?</h2>
            <p>Join our community of learners and mentors today</p>
            <div className="cta-buttons">
              <button 
                onClick={() => loginWithRedirect({ screen_hint: 'signup' })}
                className="cta-button cta-button-primary"
              >
                Get Started Free
              </button>
              <button 
                onClick={() => loginWithRedirect()}
                className="cta-button cta-button-secondary"
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-logo">
              <AcademicCapIcon className="footer-logo-icon" />
              <span>BuildBytes LMS</span>
            </div>
            <p className="footer-tagline">
              Empowering learners through technology and collaboration
            </p>
          </div>
        </div>
      </footer>
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
    return <LandingPage />;
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