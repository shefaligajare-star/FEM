/**
 * FLOURISHING ENTREPRENEURS AND MENTORS (FEM)
 * Offline Form Interceptor & Local-First Action Handler
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Intercept Problem Creation when offline
  const problemForm = document.getElementById('problem-create-form');
  if (problemForm) {
    problemForm.addEventListener('submit', async (e) => {
      if (!navigator.onLine) {
        e.preventDefault();
        const formData = new FormData(problemForm);
        const payload = {
          title: formData.get('title'),
          description: formData.get('description'),
          category_id: formData.get('category'),
          industry: formData.get('industry'),
          business_stage: formData.get('business_stage'),
          urgency: formData.get('urgency'),
          desired_support: formData.get('desired_support'),
          is_rural_business: formData.has('is_rural_business'),
          location: formData.get('location')
        };

        const localId = 'prob_' + Date.now();
        await window.FEM_DB.storeLocalItem('problems', { local_id: localId, ...payload, status: 'SAVED_OFFLINE' });
        await window.FEM_DB.savePendingOperation({
          type: 'CREATE_PROBLEM',
          entity: 'PROBLEM',
          local_id: localId,
          payload: payload
        });

        alert("You're offline: Your problem has been safely saved on this device. Once connectivity returns, FEM will sync it and calculate mentor matches!");
        window.location.href = '/entrepreneur/problems/';
      }
    });
  }

  // 2. Intercept Community Post Creation when offline
  const postForm = document.getElementById('community-post-form');
  if (postForm) {
    postForm.addEventListener('submit', async (e) => {
      if (!navigator.onLine) {
        e.preventDefault();
        const formData = new FormData(postForm);
        const payload = {
          title: formData.get('title'),
          content: formData.get('content'),
          post_type: formData.get('post_type'),
          tags: formData.get('tags')
        };

        const localId = 'post_' + Date.now();
        await window.FEM_DB.storeLocalItem('posts', { local_id: localId, ...payload, status: 'SAVED_OFFLINE' });
        await window.FEM_DB.savePendingOperation({
          type: 'CREATE_POST',
          entity: 'POST',
          local_id: localId,
          payload: payload
        });

        alert("Saved offline: Your post is stored locally and will be published automatically when your connection returns.");
        window.location.reload();
      }
    });
  }

  // 3. Intercept Story Creation when offline
  const storyForm = document.getElementById('story-create-form');
  if (storyForm) {
    storyForm.addEventListener('submit', async (e) => {
      if (!navigator.onLine) {
        e.preventDefault();
        const formData = new FormData(storyForm);
        const payload = {
          story_type: formData.get('story_type'),
          title: formData.get('title'),
          business_context: formData.get('business_context'),
          summary: formData.get('summary'),
          what_happened: formData.get('what_happened'),
          what_i_learned: formData.get('what_i_learned'),
          what_i_would_do_differently: formData.get('what_i_would_do_differently'),
          key_takeaway: formData.get('key_takeaway')
        };

        const localId = 'story_' + Date.now();
        await window.FEM_DB.storeLocalItem('stories', { local_id: localId, ...payload, status: 'SAVED_OFFLINE' });
        await window.FEM_DB.savePendingOperation({
          type: 'CREATE_STORY',
          entity: 'STORY',
          local_id: localId,
          payload: payload
        });

        alert("Saved offline: Your story has been saved locally and will sync when you're back online.");
        window.location.href = '/stories/';
      }
    });
  }

  // 4. Intercept Collaboration Request Creation when offline
  const collabForm = document.getElementById('collab-create-form');
  if (collabForm) {
    collabForm.addEventListener('submit', async (e) => {
      if (!navigator.onLine) {
        e.preventDefault();
        const formData = new FormData(collabForm);
        const payload = {
          title: formData.get('title'),
          description: formData.get('description'),
          industry: formData.get('industry'),
          collaboration_type: formData.get('collaboration_type'),
          location: formData.get('location'),
          tags: formData.get('tags')
        };

        const localId = 'collab_' + Date.now();
        await window.FEM_DB.storeLocalItem('collaborations', { local_id: localId, ...payload, status: 'SAVED_OFFLINE' });
        await window.FEM_DB.savePendingOperation({
          type: 'CREATE_COLLABORATION',
          entity: 'COLLABORATION',
          local_id: localId,
          payload: payload
        });

        alert("Saved offline: Your collaboration request will automatically sync and appear on the board once connected.");
        window.location.href = '/collaborate/';
      }
    });
  }
});
