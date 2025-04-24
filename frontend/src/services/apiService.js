// src/services/apiService.js

import axios from 'axios';

// Set base URL for API requests
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  // For development testing, we're not using auth
  // In production, get token from Clerk
  config.headers.Authorization = `Bearer test-token`;
  return config;
});

// Chat service functions
const chatService = {
  // Send a message to the RAG system
  sendMessage: async (message) => {
    try {
      // Get user ID (in production, from Clerk)
      const userId = localStorage.getItem('user_id') || 'demo-user';
      
      const response = await api.post('/chat', {
        message,
        user_id: userId,
      });
      
      return response.data.response;
    } catch (error) {
      console.error('Error sending message:', error);
      throw new Error('Failed to send message. Please try again.');
    }
  },
  
  // Get chat history
  getChatHistory: async () => {
    try {
      const response = await api.get('/chat/history');
      return response.data.history;
    } catch (error) {
      console.error('Error fetching chat history:', error);
      return [];
    }
  },
};

// Analytics service functions
const analyticsService = {
  // Get analytics data
  getAnalytics: async (params = {}) => {
    try {
      const response = await api.post('/analytics', params);
      return response.data;
    } catch (error) {
      console.error('Error fetching analytics:', error);
      throw new Error('Failed to load analytics data.');
    }
  },
  
  // Get recommendations
  getRecommendations: async (postType = null) => {
    try {
      const params = postType ? { post_type: postType } : {};
      const response = await api.get('/recommendations', { params });
      return response.data.recommendations;
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      return [];
    }
  },
  
  // Get best posting times
  getBestTimes: async (postType = null) => {
    try {
      const params = postType ? { post_type: postType } : {};
      const response = await api.get('/best-times', { params });
      return postType ? response.data.best_time : response.data.best_times;
    } catch (error) {
      console.error('Error fetching best times:', error);
      return null;
    }
  },
  
  // Get metrics summary
  getMetricsSummary: async () => {
    try {
      const response = await api.get('/metrics/summary');
      return response.data;
    } catch (error) {
      console.error('Error fetching metrics summary:', error);
      return null;
    }
  },
  
  // Upload new data
  uploadData: async (formData) => {
    try {
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading data:', error);
      throw new Error('Failed to upload data. Please try again.');
    }
  },
};

// Auth service for Clerk integration
const authService = {
  // Set auth token from Clerk
  setToken: (token) => {
    localStorage.setItem('auth_token', token);
  },
  
  // Clear auth token
  clearToken: () => {
    localStorage.removeItem('auth_token');
  },
  
  // Set user ID
  setUserId: (userId) => {
    localStorage.setItem('user_id', userId);
  },
  
  // Get user ID
  getUserId: () => {
    return localStorage.getItem('user_id');
  },
};

export { chatService, analyticsService, authService };