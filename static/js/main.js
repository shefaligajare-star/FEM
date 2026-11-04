/**
 * FLOURISHING ENTREPRENEURS AND MENTORS (FEM)
 * Main Application Script & Interactions
 */

// Helper to get Django CSRF Cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Register PWA Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/service-worker.js')
      .then(reg => {
        // Service worker registered
      })
      .catch(err => {
        console.warn('ServiceWorker registration note:', err);
      });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  // Alert dismiss buttons
  document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      if (alert) alert.remove();
    });
  });

  // Post Like AJAX
  document.querySelectorAll('.like-post-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const postId = btn.dataset.postId;
      if (!postId) return;

      if (!navigator.onLine) {
        alert("You're offline. Reactions will synchronize when connectivity returns.");
        if (window.FEM_DB) {
          window.FEM_DB.savePendingOperation({
            type: 'LIKE_POST',
            entity: 'POST',
            payload: { post_id: postId }
          });
        }
        return;
      }

      try {
        const res = await fetch(`/community/${postId}/react/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        const data = await res.json();
        if (data.status === 'ok') {
          const countSpan = btn.querySelector('.like-count');
          if (countSpan) countSpan.textContent = data.likes_count;
          btn.classList.toggle('liked', data.reacted);
        }
      } catch (err) {
        console.error('Like error:', err);
      }
    });
  });

  // Story Like AJAX
  document.querySelectorAll('.like-story-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const storyId = btn.dataset.storyId;
      if (!storyId) return;

      if (!navigator.onLine) {
        alert("Saved offline. Your appreciation will sync when you return online.");
        return;
      }

      try {
        const res = await fetch(`/stories/${storyId}/like/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        const data = await res.json();
        if (data.status === 'ok') {
          const countSpan = btn.querySelector('.like-count');
          if (countSpan) countSpan.textContent = data.likes_count;
          btn.classList.toggle('liked', data.liked);
        }
      } catch (err) {
        console.error('Story like error:', err);
      }
    });
  });
});
