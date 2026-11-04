/**
 * FLOURISHING ENTREPRENEURS AND MENTORS (FEM)
 * Client-Side IndexedDB Storage Layer for Offline-First Operation
 */

const DB_NAME = 'FEM_Offline_DB';
const DB_VERSION = 1;

let dbPromise = null;

function getIndexedDB() {
  if (!dbPromise) {
    dbPromise = new Promise((resolve, reject) => {
      if (!window.indexedDB) {
        console.warn('IndexedDB not supported on this browser.');
        resolve(null);
        return;
      }

      const request = window.indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Pending operations queue for auto-sync
        if (!db.objectStoreNames.contains('pending_operations')) {
          const store = db.createObjectStore('pending_operations', { keyPath: 'operation_id' });
          store.createIndex('created_at', 'created_at', { unique: false });
          store.createIndex('status', 'status', { unique: false });
        }

        // Entity offline stores
        if (!db.objectStoreNames.contains('posts')) {
          db.createObjectStore('posts', { keyPath: 'local_id' });
        }
        if (!db.objectStoreNames.contains('problems')) {
          db.createObjectStore('problems', { keyPath: 'local_id' });
        }
        if (!db.objectStoreNames.contains('stories')) {
          db.createObjectStore('stories', { keyPath: 'local_id' });
        }
        if (!db.objectStoreNames.contains('collaborations')) {
          db.createObjectStore('collaborations', { keyPath: 'local_id' });
        }
        if (!db.objectStoreNames.contains('messages')) {
          db.createObjectStore('messages', { keyPath: 'local_id' });
        }
        if (!db.objectStoreNames.contains('cached_data')) {
          db.createObjectStore('cached_data', { keyPath: 'key' });
        }
      };

      request.onsuccess = (event) => resolve(event.target.result);
      request.onerror = (event) => {
        console.error('IndexedDB open error:', event.target.error);
        reject(event.target.error);
      };
    });
  }
  return dbPromise;
}

// Helper functions for pending sync operations
async function savePendingOperation(operation) {
  const db = await getIndexedDB();
  if (!db) return false;

  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending_operations', 'readwrite');
    const store = tx.objectStore('pending_operations');
    const req = store.put({
      operation_id: operation.operation_id || 'op_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      type: operation.type,
      entity: operation.entity,
      local_id: operation.local_id || 'loc_' + Date.now(),
      payload: operation.payload || {},
      created_at: operation.created_at || new Date().toISOString(),
      status: 'PENDING'
    });

    req.onsuccess = () => resolve(true);
    req.onerror = () => reject(req.error);
  });
}

async function getPendingOperations() {
  const db = await getIndexedDB();
  if (!db) return [];

  return new Promise((resolve) => {
    const tx = db.transaction('pending_operations', 'readonly');
    const store = tx.objectStore('pending_operations');
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => resolve([]);
  });
}

async function removePendingOperation(operationId) {
  const db = await getIndexedDB();
  if (!db) return;

  return new Promise((resolve) => {
    const tx = db.transaction('pending_operations', 'readwrite');
    const store = tx.objectStore('pending_operations');
    const req = store.delete(operationId);
    req.onsuccess = () => resolve(true);
    req.onerror = () => resolve(false);
  });
}

// Offline Entity Storage
async function storeLocalItem(storeName, item) {
  const db = await getIndexedDB();
  if (!db) return;

  return new Promise((resolve) => {
    const tx = db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    const req = store.put(item);
    req.onsuccess = () => resolve(true);
    req.onerror = () => resolve(false);
  });
}

async function getLocalItems(storeName) {
  const db = await getIndexedDB();
  if (!db) return [];

  return new Promise((resolve) => {
    const tx = db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => resolve([]);
  });
}

window.FEM_DB = {
  savePendingOperation,
  getPendingOperations,
  removePendingOperation,
  storeLocalItem,
  getLocalItems
};
