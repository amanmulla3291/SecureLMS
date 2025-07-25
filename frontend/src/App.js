import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
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
  TrashIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

// Auth Provider
function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in on app start
    const token = localStorage.getItem('auth_token');
    if (token) {
      // Verify token and get user info
      fetchUserInfo(token);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserInfo = async (token) => {
    try {
      const response = await axios.get(`${API}/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user info:', error);
      localStorage.removeItem('auth_token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, {
      email,
      password
    });
    
    const { access_token, user: userData } = response.data;
    localStorage.setItem('auth_token', access_token);
    setUser(userData);
    return userData;
  };

  const register = async (name, email, password, role = 'student') => {
    const response = await axios.post(`${API}/auth/register`, {
      name,
      email,
      password,
      role
    });
    
    const { access_token, user: userData } = response.data;
    localStorage.setItem('auth_token', access_token);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

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

// Auth Form Component
function AuthForm() {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'student'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await register(formData.name, formData.email, formData.password, formData.role);
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <AcademicCapIcon className="auth-icon" />
          <h1>BuildBytes LMS</h1>
          <p>Learning Management System for Technical Projects</p>
        </div>

        <div className="auth-tabs">
          <button
            className={`auth-tab ${isLogin ? 'active' : ''}`}
            onClick={() => setIsLogin(true)}
          >
            Sign In
          </button>
          <button
            className={`auth-tab ${!isLogin ? 'active' : ''}`}
            onClick={() => setIsLogin(false)}
          >
            Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="error-message">{error}</div>}
          
          {!isLogin && (
            <div className="form-group">
              <label>Full Name</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required={!isLogin}
                placeholder="Enter your full name"
              />
            </div>
          )}

          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="Enter your email"
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <div className="password-input">
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                placeholder={isLogin ? "Enter your password" : "Min 8 chars, 1 letter, 1 number"}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeSlashIcon className="w-5 h-5" /> : <EyeIcon className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {!isLogin && (
            <div className="form-group">
              <label>Role</label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                required
              >
                <option value="student">Student</option>
                <option value="mentor">Mentor</option>
              </select>
            </div>
          )}

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              type="button"
              className="auth-link"
              onClick={() => setIsLogin(!isLogin)}
            >
              {isLogin ? 'Sign Up' : 'Sign In'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

// Landing Page Component
function LandingPage() {
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
            <AuthForm />
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
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = React.useContext(ThemeContext);
  const location = useLocation();

  const navigation = user?.role === 'mentor' 
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
            <Link 
              key={item.name} 
              to={item.href} 
              className={`sidebar-nav-item ${location.pathname === item.href ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon className="sidebar-nav-icon" />
              {item.name}
            </Link>
          ))}
        </nav>
        
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-user-info">
              <p className="sidebar-user-name">{user?.name}</p>
              <p className="sidebar-user-role">{user?.role}</p>
            </div>
          </div>
          <button 
            onClick={logout}
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
  const { user } = useAuth();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem('auth_token');
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
  }, []);

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

  const fetchCategories = async () => {
    try {
      const token = localStorage.getItem('auth_token');
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
  }, []);

  const handleCreateCategory = async (categoryData) => {
    try {
      const token = localStorage.getItem('auth_token');
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
      const token = localStorage.getItem('auth_token');
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
        const token = localStorage.getItem('auth_token');
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

// Projects Component
function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [categories, setCategories] = useState([]);
  const { user } = useAuth();

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.get(`${API}/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.get(`${API}/subject-categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  useEffect(() => {
    fetchProjects();
    fetchCategories();
  }, []);

  const handleCreateProject = async (projectData) => {
    try {
      const token = localStorage.getItem('auth_token');
      await axios.post(`${API}/projects`, projectData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowCreateModal(false);
      fetchProjects();
    } catch (error) {
      console.error('Error creating project:', error);
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="projects">
      <div className="page-header">
        <h1 className="page-title">
          {user?.role === 'mentor' ? 'Projects' : 'My Projects'}
        </h1>
        {user?.role === 'mentor' && (
          <button 
            className="btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon className="w-5 h-5" />
            Add Project
          </button>
        )}
      </div>

      <div className="projects-grid">
        {projects.map((project) => {
          const category = categories.find(c => c.id === project.subject_category_id);
          return (
            <div key={project.id} className="project-card">
              <div className="project-header">
                <div 
                  className="project-color"
                  style={{ backgroundColor: category?.color || '#3B82F6' }}
                ></div>
                <h3>{project.title}</h3>
              </div>
              <p className="project-description">{project.description}</p>
              <div className="project-meta">
                <span className="project-category">{category?.name}</span>
                <span className="project-students">
                  {project.assigned_students?.length || 0} students
                </span>
              </div>
              <div className="project-actions">
                <button className="btn-secondary">View Details</button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Project Modal */}
      {showCreateModal && (
        <ProjectModal
          categories={categories}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateProject}
        />
      )}
    </div>
  );
}

// Project Modal Component
function ProjectModal({ categories, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    subject_category_id: '',
    assigned_students: []
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h2>Create Project</h2>
          <button onClick={onClose} className="modal-close">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>Project Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
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
            <label>Subject Category</label>
            <select
              value={formData.subject_category_id}
              onChange={(e) => setFormData({...formData, subject_category_id: e.target.value})}
              required
            >
              <option value="">Select Category</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="form-actions">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Students Component
function Students() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [progressData, setProgressData] = useState([]);

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        const response = await axios.get(`${API}/progress/overview`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setProgressData(response.data.overview);
      } catch (error) {
        console.error('Error fetching students:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStudents();
  }, []);

  if (loading) return <Loading />;

  return (
    <div className="students">
      <div className="page-header">
        <h1 className="page-title">Students</h1>
      </div>

      <div className="students-table">
        <table className="table">
          <thead>
            <tr>
              <th>Student Name</th>
              <th>Email</th>
              <th>Total Projects</th>
              <th>Completed Projects</th>
              <th>Progress</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {progressData.map((student) => (
              <tr key={student.student_id}>
                <td>{student.student_name}</td>
                <td>{student.student_email}</td>
                <td>{student.total_projects}</td>
                <td>{student.completed_projects}</td>
                <td>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${student.completion_percentage}%` }}
                    ></div>
                  </div>
                  <span>{Math.round(student.completion_percentage)}%</span>
                </td>
                <td>
                  <button className="btn-secondary btn-small">View Details</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Resources Component
function Resources() {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [categories, setCategories] = useState([]);
  const { user } = useAuth();

  const fetchResources = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.get(`${API}/resources`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setResources(response.data);
    } catch (error) {
      console.error('Error fetching resources:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.get(`${API}/subject-categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  useEffect(() => {
    fetchResources();
    fetchCategories();
  }, []);

  const handleCreateResource = async (resourceData) => {
    try {
      const token = localStorage.getItem('auth_token');
      await axios.post(`${API}/resources`, resourceData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowCreateModal(false);
      fetchResources();
    } catch (error) {
      console.error('Error creating resource:', error);
    }
  };

  if (loading) return <Loading />;

  return (
    <div className="resources">
      <div className="page-header">
        <h1 className="page-title">Resources</h1>
        {user?.role === 'mentor' && (
          <button 
            className="btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon className="w-5 h-5" />
            Add Resource
          </button>
        )}
      </div>

      <div className="resources-grid">
        {resources.map((resource) => {
          const category = categories.find(c => c.id === resource.subject_category_id);
          return (
            <div key={resource.id} className="resource-card">
              <div className="resource-header">
                <div className="resource-type-icon">
                  {resource.resource_type === 'link' ? '🔗' : 
                   resource.resource_type === 'pdf' ? '📄' : 
                   resource.resource_type === 'video' ? '🎥' : '📄'}
                </div>
                <h3>{resource.title}</h3>
              </div>
              <p className="resource-description">{resource.description}</p>
              <div className="resource-meta">
                <span className="resource-category">{category?.name}</span>
                <span className="resource-type">{resource.resource_type}</span>
              </div>
              <div className="resource-actions">
                {resource.url ? (
                  <a href={resource.url} target="_blank" rel="noopener noreferrer" className="btn-primary">
                    Open Resource
                  </a>
                ) : (
                  <button className="btn-primary">Download</button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Resource Modal */}
      {showCreateModal && (
        <ResourceModal
          categories={categories}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateResource}
        />
      )}
    </div>
  );
}

// Resource Modal Component
function ResourceModal({ categories, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    subject_category_id: '',
    resource_type: 'link',
    url: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h2>Add Resource</h2>
          <button onClick={onClose} className="modal-close">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>Resource Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
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
            <label>Subject Category</label>
            <select
              value={formData.subject_category_id}
              onChange={(e) => setFormData({...formData, subject_category_id: e.target.value})}
              required
            >
              <option value="">Select Category</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="form-group">
            <label>Resource Type</label>
            <select
              value={formData.resource_type}
              onChange={(e) => setFormData({...formData, resource_type: e.target.value})}
              required
            >
              <option value="link">Link</option>
              <option value="pdf">PDF</option>
              <option value="document">Document</option>
              <option value="video">Video</option>
            </select>
          </div>
          
          <div className="form-group">
            <label>URL</label>
            <input
              type="url"
              value={formData.url}
              onChange={(e) => setFormData({...formData, url: e.target.value})}
              placeholder="https://..."
              required={formData.resource_type === 'link'}
            />
          </div>
          
          <div className="form-actions">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Add Resource
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Settings Component
function Settings() {
  const { user } = useAuth();
  const { theme, toggleTheme } = React.useContext(ThemeContext);

  return (
    <div className="settings">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
      </div>

      <div className="settings-sections">
        <div className="settings-section">
          <h2>Appearance</h2>
          <div className="setting-item">
            <div className="setting-info">
              <h3>Theme</h3>
              <p>Choose your preferred theme</p>
            </div>
            <button onClick={toggleTheme} className="btn-secondary">
              {theme === 'light' ? (
                <>
                  <MoonIcon className="w-5 h-5" />
                  Switch to Dark
                </>
              ) : (
                <>
                  <SunIcon className="w-5 h-5" />
                  Switch to Light
                </>
              )}
            </button>
          </div>
        </div>

        <div className="settings-section">
          <h2>Account Information</h2>
          <div className="setting-item">
            <div className="setting-info">
              <h3>Name</h3>
              <p>{user?.name}</p>
            </div>
          </div>
          <div className="setting-item">
            <div className="setting-info">
              <h3>Email</h3>
              <p>{user?.email}</p>
            </div>
          </div>
          <div className="setting-item">
            <div className="setting-info">
              <h3>Role</h3>
              <p className="capitalize">{user?.role}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main App Component
function AppContent() {
  const { user, loading } = useAuth();

  if (loading) return <Loading />;

  if (!user) {
    return <LandingPage />;
  }

  return (
    <Router>
      <DashboardLayout>
        <Routes>
          <Route path="/dashboard" element={<DashboardStats />} />
          <Route path="/subjects" element={<SubjectCategories />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/students" element={<Students />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </DashboardLayout>
    </Router>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <div className="App">
          <AppContent />
        </div>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;