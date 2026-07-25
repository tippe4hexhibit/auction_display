<script>
    export let open = false;
    export let title = 'Are you sure?';
    export let message = '';
    export let confirmLabel = 'Confirm';
    export let cancelLabel = 'Cancel';
    export let onConfirm;
    export let onCancel;

    function handleWindowKeydown(e) {
        if (open && e.key === 'Escape') onCancel();
    }
</script>

<svelte:window on:keydown={handleWindowKeydown} />

<style>
    .backdrop {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .dialog {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        max-width: 420px;
        width: 90%;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .dialog h3 { margin-top: 0; }
    .dialog p { color: #333; line-height: 1.4; }
    .actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-top: 1.5rem;
    }
    .btn {
        padding: 0.6rem 1.2rem;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font: inherit;
    }
    .cancel-btn { background: #6c757d; color: white; }
    .cancel-btn:hover { background: #5a6268; }
    .confirm-btn { background: #dc3545; color: white; }
    .confirm-btn:hover { background: #c82333; }
</style>

{#if open}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="backdrop" on:click={onCancel} role="presentation">
        <div class="dialog" on:click={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title" tabindex="-1">
            <h3 id="confirm-dialog-title">{title}</h3>
            <p>{message}</p>
            <div class="actions">
                <button class="btn cancel-btn" on:click={onCancel}>{cancelLabel}</button>
                <button class="btn confirm-btn" on:click={onConfirm}>{confirmLabel}</button>
            </div>
        </div>
    </div>
{/if}
