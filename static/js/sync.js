/**
 * FLOURISHING ENTREPRENEURS AND MENTORS (FEM)
 * Offline-First Synchronization Controller
 */

const FEM_Sync = {
  isSyncing: false,

  init() {
    this.updateOnlineStatus();
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());

    // Check pending operations on start
    this.checkPendingQueue();

    // Attach sync modal trigger
    const syncIndicator = document.getElementById('sync-status-indicator');
    if (syncIndicator) {
      syncIndicator.addEventListener('click', () => this.openSyncModal());
    }

    const modalClose = document.getElementById('sync-modal-close');
    if (modalClose) {
      modalClose.addEventListener('click', () => this.closeSyncModal());
    }

    const manualSyncBtn = document.getElementById('manual-sync-trigger');
    if (manualSyncBtn) {
      manualSyncBtn.addEventListener('click', () => this.drainQueue());
    }
  },

  handleOnline() {
    this.showBanner('Back online — syncing your changes…', 'banner-syncing');
    this.updateIndicator('syncing', 'Syncing…');
    this.drainQueue();
  },

  handleOffline() {
    this.showBanner("You're offline — changes will save locally and sync automatically.", 'banner-offline');
    this.updateIndicator('offline', 'Saved offline');
  },

  showBanner(message, className) {
    const banner = document.getElementById('offline-banner');
    if (!banner) return;

    banner.className = `offline-banner visible ${className}`;
    banner.innerHTML = `<span>${message}</span>`;

    if (className === 'banner-synced') {
      setTimeout(() => {
        banner.className = 'offline-banner';
      }, 4000);
    }
  },

  updateIndicator(state, text) {
    const indicator = document.getElementById('sync-status-indicator');
    const dot = document.getElementById('sync-dot');
    const label = document.getElementById('sync-label');

    if (!indicator || !dot || !label) return;

    dot.className = `sync-dot ${state}`;
    label.textContent = text;
  },

  async checkPendingQueue() {
    if (!window.FEM_DB) return;
    const ops = await window.FEM_DB.getPendingOperations();

    if (!navigator.onLine) {
      this.updateIndicator('offline', ops.length > 0 ? `${ops.length} saved offline` : 'Offline');
      this.showBanner("You're offline — changes will save locally and sync automatically.", 'banner-offline');
    } else if (ops.length > 0) {
      this.updateIndicator('syncing', `Syncing ${ops.length} items…`);
      this.drainQueue();
    } else {
      this.updateIndicator('synced', 'Synced');
    }
  },

  async drainQueue() {
    if (this.isSyncing || !navigator.onLine || !window.FEM_DB) return;
    this.isSyncing = true;

    try {
      const ops = await window.FEM_DB.getPendingOperations();
      if (ops.length === 0) {
        this.updateIndicator('synced', 'Synced');
        this.isSyncing = false;
        return;
      }

      this.updateIndicator('syncing', `Syncing ${ops.length} items…`);

      const response = await fetch('/api/sync/batch/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ operations: ops })
      });

      if (!response.ok) {
        throw new Error(`Sync failed with status: ${response.status}`);
      }

      const data = await response.json();

      // Remove successfully processed items from queue
      if (data.results) {
        for (const item of data.results) {
          if (item.status === 'SYNCED' || item.status === 'ALREADY_SYNCED') {
            await window.FEM_DB.removePendingOperation(item.operation_id);
          }
        }
      }

      const remaining = await window.FEM_DB.getPendingOperations();
      if (remaining.length === 0) {
        this.updateIndicator('synced', 'Synced');
        this.showBanner('Everything is synced.', 'banner-synced');
      } else {
        this.updateIndicator('failed', `${remaining.length} pending retry`);
      }

      // Refresh any list views if data changed
      if (data.synced_count > 0 && window.location.pathname.includes('/community/')) {
        setTimeout(() => window.location.reload(), 1200);
      }

    } catch (err) {
      console.warn('Sync queue drain error:', err);
      this.updateIndicator('failed', 'Sync failed — retrying');
    } finally {
      this.isSyncing = false;
      this.refreshModalQueueList();
    }
  },

  updateOnlineStatus() {
    if (navigator.onLine) {
      this.updateIndicator('synced', 'Synced');
    } else {
      this.handleOffline();
    }
  },

  async openSyncModal() {
    const modal = document.getElementById('sync-modal-backdrop');
    if (!modal) return;
    modal.classList.add('active');
    await this.refreshModalQueueList();
  },

  closeSyncModal() {
    const modal = document.getElementById('sync-modal-backdrop');
    if (modal) modal.classList.remove('active');
  },

  async refreshModalQueueList() {
    const list = document.getElementById('sync-queue-list');
    if (!list || !window.FEM_DB) return;

    const ops = await window.FEM_DB.getPendingOperations();
    if (ops.length === 0) {
      list.innerHTML = `
        <div style="padding: 1.5rem; text-align: center; color: var(--text-muted);">
          <p>🟢 All changes are synchronized with the server.</p>
          <small>Offline queue is empty.</small>
        </div>
      `;
      return;
    }

    list.innerHTML = ops.map(op => `
      <div class="sync-queue-item">
        <div>
          <strong>${op.type.replace('_', ' ')}</strong>
          <div style="font-size: 0.75rem; color: var(--text-muted);">ID: ${op.operation_id.substr(0, 16)}...</div>
        </div>
        <span class="badge badge-amber">Saved Offline</span>
      </div>
    `).join('');
  }
};

document.addEventListener('DOMContentLoaded', () => FEM_Sync.init());
window.FEM_Sync = FEM_Sync;
