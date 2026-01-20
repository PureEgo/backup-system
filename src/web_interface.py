"""
Web Interface Module - Enhanced Version
Flask-based web interface with authentication, charts, and search
"""

from flask import Flask, request, jsonify, send_file, Response, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import os
import logging
from datetime import datetime
import hashlib

from .backup_orchestrator import BackupOrchestrator
from .scheduler import BackupScheduler
from .notification_service import NotificationService


# Simple authentication (for production use proper password hashing!)
USERS = {
    'admin': hashlib.sha256('admin123'.encode()).hexdigest(),  # Password: admin123
    'user': hashlib.sha256('user123'.encode()).hexdigest()      # Password: user123
}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


# Enhanced Dashboard HTML with Chart.js, Search, and Authentication
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database Backup System - Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
            min-height: 100vh;
            padding: 20px;
            color: #e0e0e0;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        
        /* Login Screen */
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .login-box {
            background: rgba(20, 25, 40, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            max-width: 400px;
            width: 100%;
        }
        .login-box h1 {
            color: #00d4ff;
            margin-bottom: 10px;
            font-size: 2em;
            text-shadow: 0 0 20px rgba(129, 140, 248, 0.5);
        }
        .login-box p {
            color: #9ca3af;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #d1d5db;
            font-weight: 600;
        }
        .form-group input {
            width: 100%;
            padding: 12px;
            background: rgba(30, 30, 45, 0.5);
            border: 2px solid rgba(99, 102, 241, 0.3);
            border-radius: 8px;
            font-size: 1em;
            color: #e0e0e0;
            transition: all 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #00d4ff;
            background: rgba(30, 30, 45, 0.8);
            box-shadow: 0 0 15px rgba(129, 140, 248, 0.2);
        }
        .login-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #00d4ff 0%, #00a8e8 100%);
            color: rgba(20, 25, 40, 0.8);
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        }
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
        }
        .login-error {
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.4);
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: none;
        }
        .login-info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 0.9em;
            color: #1976d2;
        }
        
        /* Dashboard */
        .hidden { display: none !important; }
        .header {
            background: rgba(20, 25, 40, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header-left h1 {
            color: #00d4ff;
            font-size: 2.5em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .header-left p { color: #9ca3af; font-size: 1.1em; }
        .header-right {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .user-info {
            text-align: right;
            margin-right: 15px;
        }
        .username {
            font-weight: 600;
            color: #e0e0e0;
        }
        .logout-btn {
            padding: 10px 20px;
            background: #ef4444;
            color: rgba(20, 25, 40, 0.8);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }
        .logout-btn:hover {
            background: #dc2626;
            transform: translateY(-2px);
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: #10b981;
            color: rgba(20, 25, 40, 0.8);
            border-radius: 50px;
            font-size: 0.9em;
            font-weight: 600;
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.8; } }
        .status-badge.offline { background: #ef4444; }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(20, 25, 40, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
        }
        .stat-card .icon { font-size: 2.5em; margin-bottom: 10px; }
        .stat-card h3 {
            color: #9ca3af;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: #00d4ff;
        }
        .stat-card .subtext { color: #999; font-size: 0.85em; margin-top: 5px; }
        
        /* Chart Section */
        .chart-section {
            background: rgba(20, 25, 40, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            position: relative;
            z-index: 0;
        }
        .chart-section h2 { color: #e0e0e0; margin-bottom: 20px; font-size: 1.5em; }
        #backupChart { max-height: 300px; }
        
        /* Actions */
        .actions {
            background: rgba(20, 25, 40, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            position: relative;
            z-index: 0;
        }
        .actions h2 { color: #e0e0e0; margin-bottom: 20px; font-size: 1.5em; }
        .button-group { display: flex; flex-wrap: wrap; gap: 15px; }
        .btn {
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            color: rgba(20, 25, 40, 0.8);
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); }
        .btn:active { transform: translateY(0); }
        .btn-primary { background: linear-gradient(135deg, #00d4ff 0%, #00a8e8 100%); }
        .btn-success { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
        .btn-danger { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
        .btn-info { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); }
        
        /* Search */
        .search-box {
            background: rgba(20, 25, 40, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            position: relative;
            z-index: 0;
        }
        .search-input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-size: 1em;
            transition: border 0.2s;
        }
        .search-input:focus {
            outline: none;
            border-color: #00d4ff;
        }
        
        /* Backups Section */
        .backups-section {
            background: rgba(20, 25, 40, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            position: relative;
            z-index: 0;
        }
        .backups-section h2 { color: #e0e0e0; margin-bottom: 20px; font-size: 1.5em; }
        .backup-table { width: 100%; border-collapse: collapse; overflow: hidden; border-radius: 10px; }
        .backup-table thead { background: linear-gradient(135deg, #00d4ff 0%, #00a8e8 100%); color: rgba(20, 25, 40, 0.8); }
        .backup-table th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }
        .backup-table td { padding: 15px; border-bottom: 1px solid #2d3748; }
        .backup-table tbody tr { transition: background 0.2s; }
        .backup-table tbody tr:hover { background: rgba(0, 212, 255, 0.1); }
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .badge-success { background: #d1fae5; color: #065f46; }
        .action-btn {
            padding: 8px 15px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.85em;
            font-weight: 600;
            transition: all 0.2s;
            margin-right: 5px;
            color: rgba(20, 25, 40, 0.8);
        }
        .action-btn:hover { transform: scale(1.05); }
        .action-btn.download { background: #3b82f6; }
        .action-btn.restore { background: #10b981; }
        
        /* Loading & Notification */
        .loading { display: none; text-align: center; padding: 20px; }
        .loading.active { display: block; }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #00d4ff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 10px;
            color: rgba(20, 25, 40, 0.8);
            font-weight: 600;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transform: translateX(400px);
            transition: transform 0.3s;
            z-index: 1000;
        }
        .notification.show { transform: translateX(0); }
        .notification.success { background: #10b981; }
        .notification.error { background: #ef4444; }
        .notification.info { background: #3b82f6; }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            backdrop-filter: blur(10px);
            z-index: 999999 !important;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .modal.active { display: flex !important; }
        
        .modal-content {
            background: linear-gradient(135deg, rgba(20, 25, 40, 0.98) 0%, rgba(30, 35, 50, 0.98) 100%);
            color: #e0e0e0;
            border-radius: 20px;
            border: 1px solid rgba(0, 212, 255, 0.2);
            padding: 35px;
            max-width: 650px;
            width: 90%;
            max-height: 85vh;
            overflow-y: auto;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(0, 212, 255, 0.1);
            position: relative;
            animation: modalSlideIn 0.3s ease-out;
        }
        @keyframes modalSlideIn {
            from { opacity: 0; transform: translateY(-30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        /* Custom Scrollbar for Modal */
        .modal-content::-webkit-scrollbar {
            width: 8px;
        }
        .modal-content::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
        }
        .modal-content::-webkit-scrollbar-thumb {
            background: rgba(0, 212, 255, 0.4);
            border-radius: 10px;
        }
        .modal-content::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 212, 255, 0.6);
        }
        .modal-content h3 { 
            color: #00d4ff; 
            margin-bottom: 20px; 
            font-size: 1.6em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        @media (max-width: 768px) {
            .stats-grid { grid-template-columns: 1fr; }
            .button-group { flex-direction: column; }
            .btn { width: 100%; justify-content: center; }
            .header { flex-direction: column; text-align: center; }
            .header-right { margin-top: 20px; }
        }
    </style>
</head>
<body>
    <!-- Login Screen -->
    <div class="login-container" id="loginScreen">
        <div class="login-box">
            <h1>💾 Login</h1>
            <p>Database Backup System</p>
            <div class="login-error" id="loginError"></div>
            <form id="loginForm" onsubmit="return login(event)">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" required autocomplete="username">
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" required autocomplete="current-password">
                </div>
                <button type="submit" class="login-btn">Login</button>
            </form>
            <div class="login-info">
                <strong>Demo credentials:</strong><br>
                Username: <code>admin</code> / Password: <code>admin123</code><br>
                Username: <code>user</code> / Password: <code>user123</code>
            </div>
        </div>
    </div>

    <!-- Dashboard -->
    <div class="container hidden" id="dashboardScreen">
        <div class="header">
            <div class="header-left">
                <h1>
                    💾 Database Backup System
                    <span class="status-badge" id="statusBadge"><span>●</span> Online</span>
                </h1>
                <p>Automated backup and restore solution</p>
            </div>
            <div class="header-right">
                <div class="user-info">
                    <div class="username" id="currentUser">User</div>
                    <div style="font-size: 0.85em; color: #999;">Administrator</div>
                </div>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📊</div>
                <h3>Total Backups</h3>
                <div class="value" id="totalBackups">-</div>
                <div class="subtext">All time</div>
            </div>
            <div class="stat-card">
                <div class="icon">💽</div>
                <h3>Total Size</h3>
                <div class="value" id="totalSize">-</div>
                <div class="subtext">Compressed</div>
            </div>
            <div class="stat-card">
                <div class="icon">🗄️</div>
                <h3>Databases</h3>
                <div class="value" id="databaseCount">-</div>
                <div class="subtext">Connected</div>
            </div>
            <div class="stat-card">
                <div class="icon">⏱️</div>
                <h3>Last Backup</h3>
                <div class="value" id="lastBackup" style="font-size: 1.2em;">-</div>
                <div class="subtext">Time ago</div>
            </div>
        </div>
        
        <div class="chart-section">
            <h2>📈 Backup History</h2>
            <canvas id="backupChart"></canvas>
        </div>
        
        <div class="actions">
        
        <!-- Notifications Panel -->
        <div class="actions" style="margin-bottom: 30px;">
            <h2 style="display: flex; align-items: center; gap: 10px;">
                📧 Notifications
                <span id="notificationsStatusBadge" class="status-badge" style="font-size: 0.7em;">⚪ Unknown</span>
            </h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div class="stat-card" style="background: rgba(20, 25, 40, 0.6);">
                    <div class="stat-icon">📧</div>
                    <h3>EMAIL</h3>
                    <div class="value" id="emailStatus">Disabled</div>
                    <div class="label" id="emailLabel">Not configured</div>
                </div>
                
                <div class="stat-card" style="background: rgba(20, 25, 40, 0.6);">
                    <div class="stat-icon">💬</div>
                    <h3>TELEGRAM</h3>
                    <div class="value" id="telegramStatus">Disabled</div>
                    <div class="label" id="telegramLabel">Not configured</div>
                </div>
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" onclick="openNotificationsConfig()">
                    ⚙️ Configure Notifications
                </button>
                <button class="btn btn-info" onclick="testNotifications('both')">
                    🧪 Send Test
                </button>
                <button class="btn btn-info" onclick="refreshNotificationsStatus()">
                    🔄 Refresh Status
                </button>
            </div>
        </div>
        
        <!-- Scheduler Panel -->
        <div class="actions" style="margin-bottom: 30px;">
            <h2 style="display: flex; align-items: center; gap: 10px;">
                ⏰ Scheduler
                <span id="schedulerStatusBadge" class="status-badge" style="font-size: 0.7em;">⚪ Unknown</span>
            </h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div class="stat-card" style="background: rgba(20, 25, 40, 0.6);">
                    <div class="stat-icon">📅</div>
                    <h3>INTERVAL</h3>
                    <div class="value" id="schedulerInterval">-</div>
                    <div class="label">Schedule frequency</div>
                </div>
                
                <div class="stat-card" style="background: rgba(20, 25, 40, 0.6);">
                    <div class="stat-icon">🕐</div>
                    <h3>NEXT RUN</h3>
                    <div class="value" id="schedulerNextRun" style="font-size: 0.8em;">-</div>
                    <div class="label">Scheduled time</div>
                </div>
            </div>
            
            <div class="button-group">
                <button class="btn btn-success" id="schedulerStartBtn" onclick="startScheduler()" style="display: none;">
                    ▶️ Start Scheduler
                </button>
                <button class="btn btn-danger" id="schedulerStopBtn" onclick="stopScheduler()" style="display: none;">
                    ⏹️ Stop Scheduler
                </button>
                <button class="btn btn-primary" onclick="runSchedulerNow()">
                    ▶️ Run Now
                </button>
                <button class="btn btn-info" onclick="refreshSchedulerStatus()">
                    🔄 Refresh Status
                </button>
            </div>
        </div>
        
        <!-- Notifications Config Modal -->
        
            <h2>🚀 Quick Actions</h2>
            <div class="button-group">
                <button class="btn btn-primary" onclick="showBackupModal()">
                    <span>📦</span> Create Backup Now
                </button>
                <button class="btn btn-success" onclick="showRestoreModal()">
                    <span>♻️</span> Restore Database
                </button>
                <button class="btn btn-info" onclick="refreshData()">
                    <span>🔄</span> Refresh
                </button>
            </div>
        </div>
        
        <!-- Backup Selection Modal -->
        <div id="backupModal" class="modal" style="display: none;">
            <div class="modal-content">
                <h3 style="margin-bottom: 10px;">💾 Create Backup</h3>
                <p style="color: #9ca3af; margin-bottom: 20px;">Select databases to backup:</p>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 8px; background: rgba(0, 212, 255, 0.1); border-radius: 6px;">
                        <input type="checkbox" id="backupAllDatabases" onchange="toggleAllDatabases()" style="margin-right: 10px; width: 18px; height: 18px; cursor: pointer;">
                        <strong style="color: #00d4ff;">Select All Databases</strong>
                    </label>
                </div>
                
                <div id="databaseCheckboxes" style="max-height: 250px; overflow-y: auto; margin-bottom: 20px; padding: 12px; background: rgba(30, 30, 45, 0.6); border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.2);">
                    <div style="text-align: center; padding: 20px; color: #9ca3af;">Loading databases...</div>
                </div>
                
                <div style="display: flex; gap: 10px;">
                    <button class="btn btn-primary" onclick="createSelectedBackup()" style="flex: 1;">
                        Create Backup
                    </button>
                    <button class="btn" onclick="closeBackupModal()" style="flex: 1; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); color: #ffffff;">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
        
        <div class="search-box">
            <input type="text" class="search-input" id="searchInput" placeholder="🔍 Search backups by database name or filename..." onkeyup="filterTable()">
        </div>
        
        <div class="loading" id="loadingIndicator">
            <div class="spinner"></div>
            <p style="margin-top: 10px; color: rgba(20, 25, 40, 0.8); font-weight: 600;">Processing...</p>
        </div>
        
        <div class="backups-section">
            <h2>📁 Recent Backups</h2>
            <table class="backup-table">
                <thead>
                    <tr>
                        <th style="width: 50px;">#</th>
                        <th>Database</th>
                        <th>Filename</th>
                        <th>Size</th>
                        <th>Created</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="backupsTableBody">
                    <tr>
                        <td colspan="7" style="text-align: center; padding: 30px; color: #999;">Loading backups...</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <div class="modal" id="restoreModal">
        <div class="modal-content">
            <h3>♻️ Restore Database</h3>
            <div class="form-group">
                <label for="restoreDatabase">Select Database</label>
                <select id="restoreDatabase" class="search-input"><option value="">Loading...</option></select>
            </div>
            <div class="form-group">
                <label for="restoreBackup">Select Backup</label>
                <select id="restoreBackup" class="search-input"><option value="">Loading...</option></select>
            </div>
            <div class="button-group">
                <button class="btn btn-success" onclick="restoreDatabase()"><span>♻️</span> Restore</button>
                <button class="btn btn-danger" onclick="closeRestoreModal()"><span>✖</span> Cancel</button>
            </div>
        </div>
    </div>
        <div id="notificationsModal" class="modal" style="display: none;">
            <div class="modal-content" style="max-width: 700px; max-height: 90vh; overflow-y: auto;">
                <h3 style="margin-bottom: 10px;">📧 Configure Notifications</h3>
                <p style="color: #9ca3af; margin-bottom: 20px;">Set up email and Telegram notifications</p>
                
                <!-- Email Configuration -->
                <div style="margin-bottom: 25px;">
                    <h4 style="color: #ffffff; margin-bottom: 15px;">📧 Email Notifications</h4>
                    
                    <div style="margin-bottom: 15px;">
                        <label style="display: flex; align-items: center; cursor: pointer; padding: 10px; background: rgba(0, 212, 255, 0.1); border-radius: 8px;">
                            <input type="checkbox" id="emailEnabled" style="margin-right: 10px; width: 18px; height: 18px;">
                            <strong>Enable Email Notifications</strong>
                        </label>
                    </div>
                    
                    <div id="emailConfigFields" style="display: none; padding: 15px; background: rgba(30, 30, 45, 0.4); border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.2);">
                        <div style="margin-bottom: 12px;">
                            <label style="display: block; margin-bottom: 5px; color: #d1d5db; font-weight: 600; font-size: 0.9em;">SMTP Server</label>
                            <input type="text" id="smtpServer" placeholder="smtp.gmail.com" style="width: 100%; padding: 10px; background: rgba(30,30,45,0.8); border: 1px solid rgba(0,212,255,0.3); border-radius: 6px; color: #fff; font-size: 0.95em;">
                        </div>
                        
                        <div style="margin-bottom: 12px;">
                            <label style="display: block; margin-bottom: 5px; color: #d1d5db; font-weight: 600; font-size: 0.9em;">SMTP Port</label>
                            <input type="number" id="smtpPort" placeholder="587" value="587" style="width: 100%; padding: 10px; background: rgba(30,30,45,0.8); border: 1px solid rgba(0,212,255,0.3); border-radius: 6px; color: #fff; font-size: 0.95em;">
                        </div>
                        
                        <div style="margin-bottom: 12px;">
                            <label style="display: block; margin-bottom: 5px; color: #d1d5db; font-weight: 600; font-size: 0.9em;">Sender Email</label>
                            <input type="email" id="senderEmail" placeholder="backup@example.com" style="width: 100%; padding: 10px; background: rgba(30,30,45,0.8); border: 1px solid rgba(0,212,255,0.3); border-radius: 6px; color: #fff; font-size: 0.95em;">
                        </div>
                        
                        <div style="margin-bottom: 12px;">
                            <label style="display: block; margin-bottom: 5px; color: #d1d5db; font-weight: 600; font-size: 0.9em;">Email Password / App Password</label>
                            <input type="password" id="emailPassword" placeholder="Enter password" style="width: 100%; padding: 10px; background: rgba(30,30,45,0.8); border: 1px solid rgba(0,212,255,0.3); border-radius: 6px; color: #fff; font-size: 0.95em;">
                            <small style="color: #9ca3af; display: block; margin-top: 5px;">For Gmail, use App Password</small>
                        </div>
                        
                        <div style="margin-bottom: 12px;">
                            <label style="display: block; margin-bottom: 5px; color: #d1d5db; font-weight: 600; font-size: 0.9em;">Recipients (comma-separated)</label>
                            <input type="text" id="emailRecipients" placeholder="admin@example.com, user@example.com" style="width: 100%; padding: 10px; background: rgba(30,30,45,0.8); border: 1px solid rgba(0,212,255,0.3); border-radius: 6px; color: #fff; font-size: 0.95em;">
                        </div>
                    </div>
                </div>
                
                <!-- Telegram Configuration -->
                <div style="margin-bottom: 25px;">
                    <h4 style="color: #ffffff; margin-bottom: 15px;">💬 Telegram Notifications</h4>
                    
                    <div style="margin-bottom: 15px;">
                        <label style="display: flex; align-items: center; cursor: pointer; padding: 10px; background: rgba(0, 212, 255, 0.1); border-radius: 8px;">
                            <input type="checkbox" id="telegramEnabled" style="margin-right: 10px; width: 18px; height: 18px;">
                            <strong>Enable Telegram Notifications</strong>
                        </label>
                    </div>
                    
                    <div id="telegramConfigFields" style="display: none; padding: 15px; background: rgba(30, 30, 45, 0.4); border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.2);">
                        <div style="margin-bottom: 12px;">
                            <label style="display: block; margin-bottom: 5px; color: #d1d5db; font-weight: 600; font-size: 0.9em;">Bot Token</label>
                            <input type="password" id="telegramBotToken" placeholder="123456789:ABCdefGHI..." style="width: 100%; padding: 10px; background: rgba(30,30,45,0.8); border: 1px solid rgba(0,212,255,0.3); border-radius: 6px; color: #fff; font-size: 0.95em;">
                            <small style="color: #9ca3af; display: block; margin-top: 5px;">Get from @BotFather on Telegram</small>
                        </div>
                        
                        <div style="margin-bottom: 12px;">
                            <label style="display: block; margin-bottom: 5px; color: #d1d5db; font-weight: 600; font-size: 0.9em;">Chat IDs (comma-separated)</label>
                            <input type="text" id="telegramChatIds" placeholder="123456789, 987654321" style="width: 100%; padding: 10px; background: rgba(30,30,45,0.8); border: 1px solid rgba(0,212,255,0.3); border-radius: 6px; color: #fff; font-size: 0.95em;">
                            <small style="color: #9ca3af; display: block; margin-top: 5px;">Get from @userinfobot on Telegram</small>
                        </div>
                    </div>
                </div>
                
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button class="btn btn-primary" onclick="saveNotificationsConfig()" style="flex: 1;">
                        💾 Save Configuration
                    </button>
                    <button class="btn btn-info" onclick="testNotifications('both')" style="flex: 1;">
                        🧪 Test
                    </button>
                    <button class="btn" onclick="closeNotificationsConfig()" 
                            style="flex: 1; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); color: #ffffff;">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    
    <div class="notification" id="notification"></div>
    
    <script>
        const API_BASE = '/api';
        let backupChart = null;
        let allBackups = [];
        
        // Authentication
        function login(event) {
            event.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('loginScreen').classList.add('hidden');
                    document.getElementById('dashboardScreen').classList.remove('hidden');
                    document.getElementById('currentUser').textContent = username;
                    refreshData();
                } else {
                    const error = document.getElementById('loginError');
                    error.textContent = data.error || 'Invalid credentials';
                    error.style.display = 'block';
                }
            })
            .catch(() => {
                const error = document.getElementById('loginError');
                error.textContent = 'Login failed';
                error.style.display = 'block';
            });
        }
        
        function logout() {
            fetch('/auth/logout', { method: 'POST' })
            .then(() => {
                document.getElementById('loginScreen').classList.remove('hidden');
                document.getElementById('dashboardScreen').classList.add('hidden');
            });
        }
        
        function checkAuth() {
            fetch('/auth/check')
            .then(res => res.json())
            .then(data => {
                if (data.authenticated) {
                    document.getElementById('loginScreen').classList.add('hidden');
                    document.getElementById('dashboardScreen').classList.remove('hidden');
                    document.getElementById('currentUser').textContent = data.username;
                    refreshData();
                }
            });
        }
        
        // Helper functions
        function showNotification(message, type = 'info') {
            const n = document.getElementById('notification');
            n.textContent = message;
            n.className = `notification ${type}`;
            n.classList.add('show');
            setTimeout(() => n.classList.remove('show'), 4000);
        }
        
        function setLoading(show) {
            document.getElementById('loadingIndicator').classList.toggle('active', show);
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }
        
        function formatRelativeTime(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const diff = now - date;
            const seconds = Math.floor(diff / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);
            if (days > 0) return `${days}d ago`;
            if (hours > 0) return `${hours}h ago`;
            if (minutes > 0) return `${minutes}m ago`;
            return `${seconds}s ago`;
        }
        
        // Extract database name from filename
        function extractDatabaseName(filename) {
            // Format: database_full_20251208_120000.sql.gz
            // Extract everything before "_full_"
            const match = filename.match(/^(.+?)_full_/);
            return match ? match[1] : 'Unknown';
        }
        
        // Load status
        async function loadStatus() {
            try {
                const response = await fetch(`${API_BASE}/status`);
                const data = await response.json();
                document.getElementById('totalBackups').textContent = data.backups?.total_count || 0;
                document.getElementById('totalSize').textContent = 
                    data.backups?.total_size_mb ? `${data.backups.total_size_mb} MB` : '0 MB';
                document.getElementById('databaseCount').textContent = data.database?.count || 0;
                document.getElementById('lastBackup').textContent = 
                    data.backups?.newest ? formatRelativeTime(data.backups.newest) : 'Never';
                const badge = document.getElementById('statusBadge');
                if (data.database?.connected) {
                    badge.classList.remove('offline');
                    badge.innerHTML = '<span>●</span> Online';
                } else {
                    badge.classList.add('offline');
                    badge.innerHTML = '<span>●</span> Offline';
                }
            } catch (error) {
                console.error('Error loading status:', error);
            }
        }
        
        // Load backups
        async function loadBackups() {
            try {
                const response = await fetch(`${API_BASE}/backups`);
                const data = await response.json();
                allBackups = data.backups || [];
                renderBackups(allBackups);
                updateChart(allBackups);
            } catch (error) {
                console.error('Error loading backups:', error);
                showNotification('Error loading backups', 'error');
            }
        }
        
        // Render backups table
        function renderBackups(backups) {
            const tbody = document.getElementById('backupsTableBody');
            if (!backups || backups.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 30px; color: #999;">No backups found. Create your first backup!</td></tr>';
                return;
            }
            tbody.innerHTML = backups.slice(0, 50).map((backup, index) => {
                const dbName = extractDatabaseName(backup.filename);
                return `
                    <tr>
                        <td style="color: #999; font-weight: 600;">${index + 1}</td>
                        <td><strong>${dbName}</strong></td>
                        <td>${backup.filename}</td>
                        <td>${formatBytes(backup.size || 0)}</td>
                        <td>${formatRelativeTime(backup.created)}</td>
                        <td><span class="badge badge-success">✓ Verified</span></td>
                        <td>
                            <button class="action-btn download" onclick="downloadBackup('${backup.filename}')">⬇️ Download</button>
                            <button class="action-btn restore" onclick="quickRestore('${dbName}', '${backup.filename}')">♻️ Restore</button>
                            <button class="action-btn delete" style="background: #ef4444;" onclick="deleteBackup('${backup.filename}')">🗑️ Delete</button>
                        </td>
                    </tr>
                `;
            }).join('');
        }
        
        // Filter table
        function filterTable() {
            const searchText = document.getElementById('searchInput').value.toLowerCase();
            const filtered = allBackups.filter(backup => {
                const dbName = extractDatabaseName(backup.filename).toLowerCase();
                const filename = backup.filename.toLowerCase();
                return dbName.includes(searchText) || filename.includes(searchText);
            });
            renderBackups(filtered);
        }
        
        // Update chart
        function updateChart(backups) {
            const ctx = document.getElementById('backupChart');
            if (!ctx) {
                console.error('Chart canvas not found');
                return;
            }
            
            if (!backups || backups.length === 0) {
                console.log('No backups to display in chart');
                return;
            }
            
            // Group by date
            const dateGroups = {};
            backups.forEach(backup => {
                try {
                    const date = new Date(backup.created).toLocaleDateString('en-US');
                    dateGroups[date] = (dateGroups[date] || 0) + 1;
                } catch (e) {
                    console.error('Error parsing date:', backup.created, e);
                }
            });
            
            // Sort dates chronologically
            const dates = Object.keys(dateGroups).sort((a, b) => {
                return new Date(a) - new Date(b);
            });
            const counts = dates.map(date => dateGroups[date]);
            
            console.log('Chart data:', { dates, counts });
            
            // Destroy previous chart if exists
            if (backupChart) {
                backupChart.destroy();
            }
            
            try {
                backupChart = new Chart(ctx, {
                    type: 'bar',  // ← Изменено с 'line' на 'bar'
                    data: {
                        labels: dates,
                        datasets: [{
                            label: 'Backups Created',
                            data: counts,
                            backgroundColor: 'rgba(102, 126, 234, 0.8)',
                            borderColor: '#00d4ff',
                            borderWidth: 2,
                            borderRadius: 8,
                            barThickness: 40
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: { 
                                display: true,
                                position: 'top'
                            },
                            tooltip: {
                                enabled: true,
                                mode: 'index',
                                intersect: false,
                                callbacks: {
                                    title: function(context) {
                                        return context[0].label;
                                    },
                                    label: function(context) {
                                        return context.dataset.label + ': ' + context.parsed.y + ' backups';
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { 
                                    stepSize: 1,
                                    precision: 0
                                },
                                grid: {
                                    display: true,
                                    color: 'rgba(0, 0, 0, 0.05)'
                                }
                            },
                            x: {
                                ticks: {
                                    maxRotation: 45,
                                    minRotation: 0
                                },
                                grid: {
                                    display: false
                                }
                            }
                        }
                    }
                });
                console.log('Chart created successfully');
            } catch (e) {
                console.error('Error creating chart:', e);
            }
        }
        
        // Actions
        let availableDatabases = [];
        
        async function showBackupModal() {
            try {
                // Load databases
                const response = await fetch(`${API_BASE}/databases`);
                const data = await response.json();
                
                if (data.databases) {
                    availableDatabases = data.databases;
                    renderDatabaseCheckboxes();
                    document.getElementById('backupModal').style.display = 'flex';
                    
                }
            } catch (error) {
                showNotification('Error loading databases', 'error');
                console.error('Error:', error);
            }
        }
        
        function renderDatabaseCheckboxes() {
            const container = document.getElementById('databaseCheckboxes');
            container.innerHTML = availableDatabases.map(db => `
                <label style="display: flex; align-items: center; margin-bottom: 8px; padding: 8px; background: rgba(20, 25, 40, 0.8); color: #e0e0e0; border-radius: 6px; cursor: pointer; transition: all 0.2s;" 
                       onmouseover="this.style.background='rgba(0, 212, 255, 0.15)'" 
                       onmouseout="this.style.background='rgba(20, 25, 40, 0.8)'">
                    <input type="checkbox" class="db-checkbox" value="${db}" style="margin-right: 10px; width: 16px; height: 16px; cursor: pointer;">
                    <span style="font-weight: 500;">${db}</span>
                </label>
            `).join('');
        }
        
        function toggleAllDatabases() {
            const allChecked = document.getElementById('backupAllDatabases').checked;
            document.querySelectorAll('.db-checkbox').forEach(cb => {
                cb.checked = allChecked;
            });
        }
        
        function closeBackupModal() {
            document.getElementById('backupModal').style.display = 'none';
            
            document.getElementById('backupAllDatabases').checked = false;
            document.querySelectorAll('.db-checkbox').forEach(cb => cb.checked = false);
        }
        
        async function createSelectedBackup() {
            const selectedDbs = Array.from(document.querySelectorAll('.db-checkbox:checked'))
                .map(cb => cb.value);
            
            if (selectedDbs.length === 0) {
                showNotification('Please select at least one database', 'error');
                return;
            }
            
            closeBackupModal();
            setLoading(true);
            
            try {
                // Always send array of databases, never null
                const response = await fetch(`${API_BASE}/backup/run`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        databases: selectedDbs  // Always send array
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    const successCount = Object.values(data.results || {}).filter(v => v).length;
                    showNotification(`✓ Backup completed! ${successCount}/${selectedDbs.length} databases backed up successfully`, 'success');
                    await refreshData();
                } else {
                    showNotification(`Error: ${data.error || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                showNotification('Error creating backup', 'error');
                console.error('Backup error:', error);
            } finally {
                setLoading(false);
            }
        }
        
        // Keep legacy function for backward compatibility
        async function createBackup() {
            showBackupModal();
        }
        
        async function showRestoreModal() {
            document.getElementById('restoreModal').classList.add('active');
            
            try {
                const dbResponse = await fetch(`${API_BASE}/databases`);
                const dbData = await dbResponse.json();
                document.getElementById('restoreDatabase').innerHTML = dbData.databases.map(db => 
                    `<option value="${db}">${db}</option>`
                ).join('');
            } catch (error) {
                showNotification('Error loading databases', 'error');
            }
            try {
                const backupResponse = await fetch(`${API_BASE}/backups`);
                const backupData = await backupResponse.json();
                document.getElementById('restoreBackup').innerHTML = backupData.backups.map(backup => 
                    `<option value="${backup.filename}">${backup.filename} (${formatBytes(backup.size)})</option>`
                ).join('');
            } catch (error) {
                showNotification('Error loading backups', 'error');
            }
        }
        
        function closeRestoreModal() {
            document.getElementById('restoreModal').classList.remove('active');
            
        }
        
        async function restoreDatabase() {
            const database = document.getElementById('restoreDatabase').value;
            const backup = document.getElementById('restoreBackup').value;
            if (!database || !backup) {
                showNotification('Please select database and backup', 'error');
                return;
            }
            if (!confirm(`Are you sure you want to restore ${database} from ${backup}?`)) return;
            closeRestoreModal();
            setLoading(true);
            try {
                const response = await fetch(`${API_BASE}/backup/restore`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ database: database, backup_file: backup })
                });
                const data = await response.json();
                if (response.ok) {
                    showNotification('✓ Database restored successfully!', 'success');
                } else {
                    showNotification(`Error: ${data.error || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                showNotification('Error restoring database', 'error');
            } finally {
                setLoading(false);
            }
        }
        
        async function quickRestore(database, filename) {
            if (!confirm(`Restore ${database} from ${filename}?`)) return;
            setLoading(true);
            try {
                const response = await fetch(`${API_BASE}/backup/restore`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ database: database, backup_file: filename })
                });
                const data = await response.json();
                if (response.ok) {
                    showNotification('✓ Database restored successfully!', 'success');
                } else {
                    showNotification(`Error: ${data.error || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                showNotification('Error restoring database', 'error');
            } finally {
                setLoading(false);
            }
        }
        
        function downloadBackup(filename) {
            window.open(`${API_BASE}/backup/download/${filename}`, '_blank');
            showNotification('Downloading backup...', 'info');
        }
        
        async function deleteBackup(filename) {
            if (!confirm(`Are you sure you want to delete backup "${filename}"?\n\nThis action cannot be undone!`)) {
                return;
            }
            
            setLoading(true);
            try {
                const response = await fetch(`${API_BASE}/backup/delete/${filename}`, {
                    method: 'DELETE'
                });
                const data = await response.json();
                
                if (response.ok) {
                    showNotification('✓ Backup deleted successfully!', 'success');
                    await refreshData();
                } else {
                    showNotification(`Error: ${data.error || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                showNotification('Error deleting backup', 'error');
                console.error('Delete error:', error);
            } finally {
                setLoading(false);
            }
        }
        
        async function refreshData() {
            await Promise.all([loadStatus(), loadBackups()]);
            showNotification('✓ Data refreshed', 'info');
        }
        

        // ===== NOTIFICATIONS FUNCTIONS =====
        
        async function refreshNotificationsStatus() {
            try {
                const response = await fetch(`${API_BASE}/notifications/status`);
                const data = await response.json();
                
                if (data.success) {
                    const s = data.status;
                    
                    // Email status
                    const emailStatus = document.getElementById('emailStatus');
                    const emailLabel = document.getElementById('emailLabel');
                    if (s.email.ready) {
                        emailStatus.textContent = 'Active';
                        emailStatus.style.color = '#10b981';
                        emailLabel.textContent = 'Ready to send';
                        emailLabel.style.color = '#10b981';
                    } else if (s.email.enabled) {
                        emailStatus.textContent = 'Enabled';
                        emailStatus.style.color = '#f59e0b';
                        emailLabel.textContent = 'Not configured';
                        emailLabel.style.color = '#f59e0b';
                    } else {
                        emailStatus.textContent = 'Disabled';
                        emailStatus.style.color = '#6b7280';
                        emailLabel.textContent = 'Not enabled';
                        emailLabel.style.color = '#6b7280';
                    }
                    
                    // Telegram status
                    const telegramStatus = document.getElementById('telegramStatus');
                    const telegramLabel = document.getElementById('telegramLabel');
                    if (s.telegram.ready) {
                        telegramStatus.textContent = 'Active';
                        telegramStatus.style.color = '#10b981';
                        telegramLabel.textContent = 'Ready to send';
                        telegramLabel.style.color = '#10b981';
                    } else if (s.telegram.enabled) {
                        telegramStatus.textContent = 'Enabled';
                        telegramStatus.style.color = '#f59e0b';
                        telegramLabel.textContent = 'Not configured';
                        telegramLabel.style.color = '#f59e0b';
                    } else {
                        telegramStatus.textContent = 'Disabled';
                        telegramStatus.style.color = '#6b7280';
                        telegramLabel.textContent = 'Not enabled';
                        telegramLabel.style.color = '#6b7280';
                    }
                    
                    // Badge
                    const badge = document.getElementById('notificationsStatusBadge');
                    if (s.any_enabled) {
                        badge.innerHTML = '● Online';
                        badge.style.background = 'rgba(16, 185, 129, 0.2)';
                        badge.style.borderColor = '#10b981';
                        badge.style.color = '#10b981';
                    } else {
                        badge.innerHTML = '● Offline';
                        badge.style.background = 'rgba(239, 68, 68, 0.2)';
                        badge.style.borderColor = '#ef4444';
                        badge.style.color = '#ef4444';
                    }
                }
            } catch (error) {
                console.error('Error fetching notifications status:', error);
            }
        }
        
        async function openNotificationsConfig() {
            try {
                const response = await fetch(`${API_BASE}/notifications/config`);
                const data = await response.json();
                
                if (data.success) {
                    const cfg = data.config;
                    
                    // Email config
                    document.getElementById('emailEnabled').checked = cfg.email.enabled;
                    document.getElementById('smtpServer').value = cfg.email.smtp_server || '';
                    document.getElementById('smtpPort').value = cfg.email.smtp_port || 587;
                    document.getElementById('senderEmail').value = cfg.email.sender || '';
                    document.getElementById('emailRecipients').value = cfg.email.recipients.join(', ');
                    document.getElementById('emailConfigFields').style.display = cfg.email.enabled ? 'block' : 'none';
                    
                    // Telegram config
                    document.getElementById('telegramEnabled').checked = cfg.telegram.enabled;
                    document.getElementById('telegramChatIds').value = cfg.telegram.chat_ids.join(', ');
                    document.getElementById('telegramConfigFields').style.display = cfg.telegram.enabled ? 'block' : 'none';
                }
                
                document.getElementById('notificationsModal').style.display = 'flex';
                
            } catch (error) {
                showNotification('✗ Error loading configuration', 'error');
            }
        }
        
        function closeNotificationsConfig() {
            document.getElementById('notificationsModal').style.display = 'none';
            
        }
        
        async function saveNotificationsConfig() {
            try {
                const emailRecipients = document.getElementById('emailRecipients').value
                    .split(',').map(e => e.trim()).filter(e => e.length > 0);
                
                const telegramChatIds = document.getElementById('telegramChatIds').value
                    .split(',').map(id => id.trim()).filter(id => id.length > 0);
                
                const config = {
                    email: {
                        enabled: document.getElementById('emailEnabled').checked,
                        smtp_server: document.getElementById('smtpServer').value,
                        smtp_port: parseInt(document.getElementById('smtpPort').value) || 587,
                        sender: document.getElementById('senderEmail').value,
                        password: document.getElementById('emailPassword').value,
                        recipients: emailRecipients,
                        use_tls: true,
                        notify_on_success: true,
                        notify_on_failure: true
                    },
                    telegram: {
                        enabled: document.getElementById('telegramEnabled').checked,
                        bot_token: document.getElementById('telegramBotToken').value,
                        chat_ids: telegramChatIds,
                        notify_on_success: true,
                        notify_on_failure: true
                    }
                };
                
                const response = await fetch(`${API_BASE}/notifications/config`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification('✓ Configuration saved successfully', 'success');
                    closeNotificationsConfig();
                    setTimeout(refreshNotificationsStatus, 1000);
                } else {
                    showNotification('✗ ' + (data.error || 'Configuration failed'), 'error');
                }
            } catch (error) {
                showNotification('✗ Error: ' + error.message, 'error');
            }
        }
        
        async function testNotifications(type) {
            setLoading(true);
            try {
                const response = await fetch(`${API_BASE}/notifications/test`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: type })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    let message = '✓ Test notification sent!';
                    if (data.results) {
                        if (data.results.email) message += '\\n📧 Email: Sent';
                        if (data.results.telegram) message += '\\n💬 Telegram: Sent';
                    }
                    showNotification(message, 'success');
                } else {
                    showNotification('✗ ' + (data.error || 'Test failed'), 'error');
                }
            } catch (error) {
                showNotification('✗ Error: ' + error.message, 'error');
            } finally {
                setLoading(false);
            }
        }
        
        // ====================================================================
        // SCHEDULER FUNCTIONS
        // ====================================================================
        
        async function refreshSchedulerStatus() {
            try {
                const response = await fetch(`${API_BASE}/scheduler/status`);
                const data = await response.json();
                
                if (data.error) {
                    console.error('Scheduler status error:', data.error);
                    return;
                }
                
                // Update status badge
                const badge = document.getElementById('schedulerStatusBadge');
                if (data.running) {
                    badge.textContent = '🟢 Running';
                    badge.style.color = '#10b981';
                    document.getElementById('schedulerStartBtn').style.display = 'none';
                    document.getElementById('schedulerStopBtn').style.display = 'inline-block';
                } else if (data.enabled) {
                    badge.textContent = '🔴 Stopped';
                    badge.style.color = '#ef4444';
                    document.getElementById('schedulerStartBtn').style.display = 'inline-block';
                    document.getElementById('schedulerStopBtn').style.display = 'none';
                } else {
                    badge.textContent = '⚪ Disabled';
                    badge.style.color = '#9ca3af';
                    document.getElementById('schedulerStartBtn').style.display = 'none';
                    document.getElementById('schedulerStopBtn').style.display = 'none';
                }
                
                // Update interval
                const intervalText = data.interval === 'daily' 
                    ? `Daily at ${data.backup_time}` 
                    : data.interval.charAt(0).toUpperCase() + data.interval.slice(1);
                document.getElementById('schedulerInterval').textContent = intervalText;
                
                // Update next run
                document.getElementById('schedulerNextRun').textContent = data.next_run || 'Not scheduled';
                
            } catch (error) {
                console.error('Error refreshing scheduler status:', error);
            }
        }
        
        async function startScheduler() {
            try {
                setLoading(true);
                const response = await fetch(`${API_BASE}/scheduler/start`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    showNotification('✅ Scheduler started', 'success');
                    await refreshSchedulerStatus();
                } else {
                    showNotification('❌ Failed to start scheduler', 'error');
                }
            } catch (error) {
                showNotification('❌ Error starting scheduler', 'error');
            } finally {
                setLoading(false);
            }
        }
        
        async function stopScheduler() {
            try {
                setLoading(true);
                const response = await fetch(`${API_BASE}/scheduler/stop`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    showNotification('⏹️ Scheduler stopped', 'success');
                    await refreshSchedulerStatus();
                } else {
                    showNotification('❌ Failed to stop scheduler', 'error');
                }
            } catch (error) {
                showNotification('❌ Error stopping scheduler', 'error');
            } finally {
                setLoading(false);
            }
        }
        
        async function runSchedulerNow() {
            if (!confirm('Run scheduled backup now?')) return;
            
            try {
                setLoading(true);
                const response = await fetch(`${API_BASE}/scheduler/run-now`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    showNotification('▶️ Backup started', 'success');
                    setTimeout(() => {
                        loadBackups();
                        updateStatus();
                    }, 2000);
                } else {
                    showNotification('❌ Failed to run backup', 'error');
                }
            } catch (error) {
                showNotification('❌ Error running backup', 'error');
            } finally {
                setLoading(false);
            }
        }
        
        // Show/hide config fields when checkboxes change
        document.addEventListener('DOMContentLoaded', function() {
            const emailEnabledCb = document.getElementById('emailEnabled');
            if (emailEnabledCb) {
                emailEnabledCb.addEventListener('change', function() {
                    document.getElementById('emailConfigFields').style.display = this.checked ? 'block' : 'none';
                });
            }
            
            const telegramEnabledCb = document.getElementById('telegramEnabled');
            if (telegramEnabledCb) {
                telegramEnabledCb.addEventListener('change', function() {
                    document.getElementById('telegramConfigFields').style.display = this.checked ? 'block' : 'none';
                });
            }
            
            // Load notifications status on page load
            refreshNotificationsStatus();
            
            // Load scheduler status on page load
            refreshSchedulerStatus();
            
            // Auto-refresh every 60 seconds
            setInterval(refreshNotificationsStatus, 60000);
            setInterval(refreshSchedulerStatus, 60000);
        });
        

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            checkAuth();
        });
    </script>
</body>
</html>"""


class WebInterface:
    """Flask web interface with authentication"""
    
    def __init__(self, config_path: str = "./config/config.json"):
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)  # Random secret key for sessions
        CORS(self.app, supports_credentials=True)
        
        self.orchestrator = BackupOrchestrator(config_path)
        
        web_config = self.orchestrator.config.get('web_interface', {})
        scheduler_config = self.orchestrator.config.get('scheduler', {})
        self.scheduler = BackupScheduler(scheduler_config, self.orchestrator.run_backup)
        
        # Initialize notification service
        notifications_config = self.orchestrator.config.get("notifications", {})
        self.notification_service = NotificationService(notifications_config)
        
        self.logger = logging.getLogger(__name__)
        
        # Setup routes ONCE at the end
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes with authentication"""
        
        # Authentication routes
        @self.app.route('/auth/login', methods=['POST'])
        def auth_login():
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if username in USERS and USERS[username] == password_hash:
                session['username'] = username
                return jsonify({'success': True, 'username': username})
            
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        @self.app.route('/auth/logout', methods=['POST'])
        def auth_logout():
            session.pop('username', None)
            return jsonify({'success': True})
        
        @self.app.route('/auth/check')
        def auth_check():
            if 'username' in session:
                return jsonify({'authenticated': True, 'username': session['username']})
            return jsonify({'authenticated': False})
        
        # Dashboard
        @self.app.route('/')
        @self.app.route('/dashboard')
        @self.app.route('/dashboard.html')
        def dashboard():
            """Render dashboard page"""
            return Response(DASHBOARD_HTML, mimetype='text/html')
    
        # ====================================================================
        # NOTIFICATIONS API
        # ====================================================================
        
        @self.app.route('/api/notifications/status')
        @login_required
        def get_notifications_status():
            """Get notifications service status"""
            try:
                config = self.orchestrator.config.get('notifications', {})
                email_enabled = config.get('email', {}).get('enabled', False)
                telegram_enabled = config.get('telegram', {}).get('enabled', False)
                
                email_configured = False
                if email_enabled:
                    ec = config.get('email', {})
                    email_configured = all([ec.get('smtp_server'), ec.get('sender'), 
                                          ec.get('password'), ec.get('recipients')])
                
                telegram_configured = False
                if telegram_enabled:
                    tc = config.get('telegram', {})
                    telegram_configured = all([tc.get('bot_token'), tc.get('chat_ids')])
                
                return jsonify({
                    'success': True,
                    'status': {
                        'email': {
                            'enabled': email_enabled,
                            'configured': email_configured,
                            'ready': email_enabled and email_configured
                        },
                        'telegram': {
                            'enabled': telegram_enabled,
                            'configured': telegram_configured,
                            'ready': telegram_enabled and telegram_configured
                        },
                        'any_enabled': email_enabled or telegram_enabled
                    }
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/notifications/config')
        @login_required
        def get_notifications_config():
            """Get current notifications configuration"""
            try:
                config = self.orchestrator.config.get('notifications', {})
                
                safe_config = {
                    'email': {
                        'enabled': config.get('email', {}).get('enabled', False),
                        'smtp_server': config.get('email', {}).get('smtp_server', ''),
                        'smtp_port': config.get('email', {}).get('smtp_port', 587),
                        'sender': config.get('email', {}).get('sender', ''),
                        'recipients': config.get('email', {}).get('recipients', []),
                        'use_tls': config.get('email', {}).get('use_tls', True),
                        'notify_on_success': config.get('email', {}).get('notify_on_success', True),
                        'notify_on_failure': config.get('email', {}).get('notify_on_failure', True),
                        'password_set': bool(config.get('email', {}).get('password'))
                    },
                    'telegram': {
                        'enabled': config.get('telegram', {}).get('enabled', False),
                        'chat_ids': config.get('telegram', {}).get('chat_ids', []),
                        'notify_on_success': config.get('telegram', {}).get('notify_on_success', True),
                        'notify_on_failure': config.get('telegram', {}).get('notify_on_failure', True),
                        'bot_token_set': bool(config.get('telegram', {}).get('bot_token'))
                    }
                }
                
                return jsonify({'success': True, 'config': safe_config})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/notifications/config', methods=['POST'])
        @login_required
        def update_notifications_config():
            """Update notifications configuration"""
            try:
                data = request.get_json()
                
                # Update config and save to file
                success = self.notification_service.update_config(data)
                
                if success:
                    # Also update orchestrator config in memory
                    self.orchestrator.config['notifications'] = data
                    return jsonify({'success': True, 'message': 'Configuration updated and saved'})
                else:
                    return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/notifications/test', methods=['POST'])
        @login_required
        def test_notifications():
            """Send test notification"""
            try:
                data = request.get_json()
                notification_type = data.get('type', 'both')
                results = {}
                
                if notification_type in ['email', 'both']:
                    email_config = self.orchestrator.config.get('notifications', {}).get('email', {})
                    if email_config.get('enabled'):
                        subject = "🔔 Test Notification - Database Backup System"
                        body = f"Test notification\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        results['email'] = self.notification_service.send_email(subject, body)
                
                if notification_type in ['telegram', 'both']:
                    telegram_config = self.orchestrator.config.get('notifications', {}).get('telegram', {})
                    if telegram_config.get('enabled'):
                        message = f"🔔 **Test Notification**\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        results['telegram'] = self.notification_service.send_telegram(message)
                
                success = any(results.values()) if results else False
                return jsonify({'success': success, 'results': results})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # SCHEDULER API
        @self.app.route('/api/scheduler/status')
        @login_required
        def get_scheduler_status():
            """Get scheduler status"""
            try:
                status = self.orchestrator.get_scheduler_status()
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/scheduler/start', methods=['POST'])
        @login_required
        def start_scheduler():
            """Start scheduler"""
            try:
                success = self.orchestrator.start_scheduler()
                return jsonify({'success': success})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/scheduler/stop', methods=['POST'])
        @login_required
        def stop_scheduler():
            """Stop scheduler"""
            try:
                success = self.orchestrator.stop_scheduler()
                return jsonify({'success': success})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/scheduler/run-now', methods=['POST'])
        @login_required
        def run_scheduler_now():
            """Run scheduler backup immediately"""
            try:
                result = self.orchestrator.run_scheduler_now()
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/scheduler/configure', methods=['POST'])
        @login_required
        def configure_scheduler():
            """Configure scheduler settings"""
            try:
                data = request.get_json()
                success = self.orchestrator.configure_scheduler(data)
                return jsonify({'success': success})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # API routes (protected)
        @self.app.route('/api')
        @login_required
        def api_info():
            return jsonify({
                'message': 'Backup System API',
                'version': '2.0.0',
                'user': session.get('username'),
                'endpoints': {
                    'status': '/api/status',
                    'backups': '/api/backups',
                    'databases': '/api/databases',
                    'run_backup': '/api/backup/run',
                    'restore': '/api/backup/restore',
                    'download': '/api/backup/download/<filename>'
                }
            })
        
        @self.app.route('/api/status')
        @login_required
        def get_status():
            try:
                status = self.orchestrator.get_system_status()
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/backups')
        @login_required
        def list_backups():
            try:
                backups = self.orchestrator.list_all_backups()
                for backup in backups:
                    backup['created'] = backup['created'].isoformat()
                    backup['modified'] = backup['modified'].isoformat()
                return jsonify({'backups': backups, 'count': len(backups)})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/databases')
        @login_required
        def list_databases():
            try:
                databases = self.orchestrator.db_connector.get_database_list()
                return jsonify({'databases': databases, 'count': len(databases)})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/backup/run', methods=['POST'])
        @login_required
        def run_backup():
            try:
                data = request.get_json() if request.is_json else {}
                databases = data.get('databases') if data else None
                results = self.orchestrator.run_backup(databases)
                
                # Notification already sent by orchestrator for each database
                
                return jsonify({
                    'status': 'completed',
                    'results': results,
                    'user': session.get('username'),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/backup/restore', methods=['POST'])
        @login_required
        def restore_backup():
            try:
                data = request.get_json()
                if not data or 'database' not in data or 'backup_file' not in data:
                    return jsonify({'error': 'Missing required parameters'}), 400
                
                database = data['database']
                backup_file = data['backup_file']
                if not backup_file.startswith('backups/'):
                    backup_file = f"backups/{backup_file}"
                
                success = self.orchestrator.restore_database(database, backup_file)
                return jsonify({
                    'success': success,
                    'database': database,
                    'backup_file': backup_file,
                    'user': session.get('username'),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/backup/download/<path:filename>')
        def download_backup(filename):
            """Download backup - no auth required for direct download"""
            try:
                # Ensure filename is safe
                filename = os.path.basename(filename)
                
                # Get absolute path to backups directory
                backup_dir = os.path.abspath(self.orchestrator.backup_manager.local_path)
                backup_path = os.path.join(backup_dir, filename)
                
                self.logger.info(f"Attempting to download: {backup_path}")
                
                if not os.path.exists(backup_path):
                    self.logger.error(f"Backup file not found: {backup_path}")
                    # Try alternate path
                    alternate_path = os.path.join('/app/backups', filename)
                    self.logger.info(f"Trying alternate path: {alternate_path}")
                    if os.path.exists(alternate_path):
                        backup_path = alternate_path
                    else:
                        return jsonify({'error': f'File not found: {filename}'}), 404
                
                self.logger.info(f"Downloading backup: {backup_path}")
                return send_file(backup_path, as_attachment=True, download_name=filename)
            except Exception as e:
                self.logger.error(f"Download error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/backup/delete/<path:filename>', methods=['DELETE'])
        @login_required
        def delete_backup(filename):
            """Delete backup file"""
            try:
                # Ensure filename is safe
                filename = os.path.basename(filename)
                
                # Get absolute path to backups directory
                backup_dir = os.path.abspath(self.orchestrator.backup_manager.local_path)
                backup_path = os.path.join(backup_dir, filename)
                
                # Try alternate path if not found
                if not os.path.exists(backup_path):
                    backup_path = os.path.join('/app/backups', filename)
                
                if not os.path.exists(backup_path):
                    self.logger.error(f"Backup file not found: {backup_path}")
                    return jsonify({'error': f'File not found: {filename}'}), 404
                
                # Delete the file
                os.remove(backup_path)
                self.logger.info(f"Backup deleted by {session.get('username')}: {filename}")
                
                return jsonify({
                    'success': True,
                    'message': f'Backup {filename} deleted successfully',
                    'deleted_by': session.get('username'),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Delete error: {str(e)}")
                return jsonify({'error': str(e)}), 500
    
    def run(self, host: str = None, port: int = None, debug: bool = None, use_reloader: bool = None):
        """Run the Flask application"""
        web_config = self.orchestrator.config.get('web_interface', {})
        host = host or web_config.get('host', '0.0.0.0')
        port = port or web_config.get('port', 5000)
        debug = False  # Always False in production
        use_reloader = False  # Always False in production
        
        if self.scheduler.enabled:
            self.scheduler.start()
        
        self.logger.info(f"Starting web interface on {host}:{port}")
        self.logger.info(f"Dashboard available at http://{host if host != '0.0.0.0' else 'localhost'}:{port}/")
        self.logger.info("Authentication enabled - Default users: admin/admin123, user/user123")
        self.app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
        