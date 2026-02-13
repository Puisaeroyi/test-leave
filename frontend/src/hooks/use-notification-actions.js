import { useState, useEffect, useCallback } from "react";
import {
  getNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead,
  deleteNotification,
  dismissAllNotifications,
} from "@api/notification-api";

const POLLING_INTERVAL = 30000; // 30 seconds

export function useNotifications() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch notifications list
  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getNotifications({ page: 1, page_size: 10 });
      setNotifications(data.results || []);
    } catch (err) {
      console.error("Failed to fetch notifications:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch unread count
  const fetchUnreadCount = useCallback(async () => {
    try {
      const count = await getUnreadCount();
      setUnreadCount(count);
    } catch (err) {
      console.error("Failed to fetch unread count:", err);
    }
  }, []);

  // Mark notification as read
  const handleMarkAsRead = useCallback(async (id) => {
    try {
      await markAsRead(id);
      // Update local state
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error("Failed to mark as read:", err);
    }
  }, []);

  // Dismiss notification - deletes from DB and removes from local view
  const dismissNotification = useCallback(async (id) => {
    try {
      // Delete from DB
      await deleteNotification(id);
      // Then remove from local state
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error("Failed to dismiss notification:", err);
    }
  }, []);

  // Dismiss all notifications - deletes all from DB and clears local view
  const dismissAll = useCallback(async () => {
    try {
      // Delete all from DB
      await dismissAllNotifications();
      // Then clear local state
      setNotifications([]);
      setUnreadCount(0);
    } catch (err) {
      console.error("Failed to dismiss all notifications:", err);
    }
  }, []);

  // Mark all as read
  const handleMarkAllAsRead = useCallback(async () => {
    try {
      await markAllAsRead();
      // Update local state
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error("Failed to mark all as read:", err);
    }
  }, []);

  // Initial fetch and polling for unread count
  useEffect(() => {
    fetchNotifications();
    fetchUnreadCount();

    // Poll unread count every 30s
    const interval = setInterval(fetchUnreadCount, POLLING_INTERVAL);

    return () => clearInterval(interval);
  }, [fetchNotifications, fetchUnreadCount]);

  return {
    notifications,
    unreadCount,
    loading,
    error,
    fetchNotifications,
    markAsRead: handleMarkAsRead,
    markAllAsRead: handleMarkAllAsRead,
    dismissNotification,
    dismissAll,
  };
}
