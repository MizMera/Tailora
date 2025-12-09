(function(){
  function ensureModal(){
    let modal = document.getElementById('confirm-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'confirm-modal';
      modal.className = 'modal-overlay';
      modal.style.display = 'none';
      modal.innerHTML = [
        '<div class="modal-card content-section">',
        '  <div class="modal-icon">⚠️</div>',
        '  <h2 class="modal-title">Confirm deletion</h2>',
        '  <p class="modal-text">Are you sure you want to delete <strong id="modal-item-name"></strong>?</p>',
        '  <p class="modal-subtext">This action cannot be undone.</p>',
        '  <div class="modal-actions">',
        '    <button type="button" class="btn btn-secondary" id="modal-cancel">Cancel</button>',
        '    <button type="button" class="btn btn-primary btn-danger-strong" id="modal-confirm">Delete permanently</button>',
        '  </div>',
        '</div>'
      ].join('');
      document.body.appendChild(modal);
    }
    return modal;
  }

  let formToSubmit = null;

  document.addEventListener('click', function(e){
    const trigger = e.target.closest('.delete-trigger');
    if (!trigger) return;
    e.preventDefault();

    const formId = trigger.getAttribute('data-form-id');
    const itemName = trigger.getAttribute('data-item-name') || 'this item';
    let form = null;
    if (formId) form = document.getElementById(formId);
    if (!form) form = trigger.closest('form');
    if (!form) return;

    formToSubmit = form;

    const modal = ensureModal();
    const nameSpan = modal.querySelector('#modal-item-name');
    const btnCancel = modal.querySelector('#modal-cancel');
    const btnConfirm = modal.querySelector('#modal-confirm');
    if (nameSpan) nameSpan.textContent = itemName;

    function closeModal(){
      modal.style.display = 'none';
      formToSubmit = null;
      modal.removeEventListener('click', onOverlay);
      document.removeEventListener('keydown', onKey);
      if (btnCancel) btnCancel.removeEventListener('click', onCancel);
      if (btnConfirm) btnConfirm.removeEventListener('click', onConfirm);
    }

    function onOverlay(ev){ if (ev.target === modal) closeModal(); }
    function onKey(ev){ if (ev.key === 'Escape' && modal.style.display === 'flex') closeModal(); }
    function onCancel(){ closeModal(); }
    function onConfirm(){ if (formToSubmit) formToSubmit.submit(); }

    if (btnCancel) btnCancel.addEventListener('click', onCancel);
    if (btnConfirm) btnConfirm.addEventListener('click', onConfirm);
    modal.addEventListener('click', onOverlay);
    document.addEventListener('keydown', onKey);

    modal.style.display = 'flex';
  });
})();
