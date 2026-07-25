<script>
    import { renderMarkdown } from '../utils/markdown.js';
    import { makeAuthenticatedRequest } from '../utils/auth.js';

    export let displayMode = 'lot';
    export let message = '';

    const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
    let draftMessage = message;
    let saving = false;

    async function saveMessage() {
        const response = await makeAuthenticatedRequest(`${API_BASE}/api/message`, {
            method: 'POST',
            body: JSON.stringify({ message: draftMessage })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save message');
        }
    }

    async function handleSave() {
        if (saving) return;
        saving = true;
        try {
            await saveMessage();
        } catch (error) {
            alert('Failed to save message: ' + error.message);
        } finally {
            saving = false;
        }
    }

    async function handleToggle() {
        if (saving) return;
        saving = true;
        try {
            const turningOn = displayMode !== 'message';
            // Turning the message screen on should never show stale/blank
            // text, so save whatever's currently drafted first.
            if (turningOn) await saveMessage();

            const response = await makeAuthenticatedRequest(`${API_BASE}/api/display-mode`, {
                method: 'POST',
                body: JSON.stringify({ display_mode: turningOn ? 'message' : 'lot' })
            });
            if (!response.ok) {
                const error = await response.json();
                alert(`Failed to update display mode: ${error.detail}`);
            }
        } catch (error) {
            alert('Failed to update display mode: ' + error.message);
        } finally {
            saving = false;
        }
    }
</script>

<style>
    .section {
        margin: 1rem 0;
        padding: 1rem;
        border: 1px solid #ccc;
        border-radius: 8px;
        background: #f9f9f9;
    }
    .section h3 { margin-top: 0; }
    .hint { margin: 0 0 0.75rem 0; font-size: 0.9rem; color: #555; }
    .status {
        margin: 0 0 1rem 0;
        font-weight: bold;
    }
    .toggle-btn {
        padding: 0.6rem 1.2rem;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font: inherit;
        color: white;
        background: #17a2b8;
        margin-bottom: 1rem;
    }
    .toggle-btn:hover:not(:disabled) { background: #138496; }
    .toggle-btn:disabled { cursor: not-allowed; opacity: 0.6; }
    textarea {
        width: 100%;
        min-height: 180px;
        padding: 0.75rem;
        font-size: 1.1rem;
        font-family: inherit;
        border: 1px solid #ccc;
        border-radius: 4px;
        box-sizing: border-box;
        resize: vertical;
    }
    .save-btn {
        margin-top: 0.75rem;
        padding: 0.6rem 1.2rem;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font: inherit;
        color: white;
        background: #007bff;
    }
    .save-btn:hover:not(:disabled) { background: #0056b3; }
    .save-btn:disabled { cursor: not-allowed; opacity: 0.6; }
    .preview-label {
        margin: 1.5rem 0 0.5rem 0;
        font-weight: bold;
    }
    .preview {
        padding: 1rem;
        border: 1px solid #ccc;
        border-radius: 4px;
        background: white;
        min-height: 3rem;
    }
</style>

<div class="section">
    <h3>Public Display Message</h3>
    <p class="hint">
        Show a blank screen with just the header and this message on the public display &mdash;
        useful before the auction starts or as a thank-you screen at the end. Supports Markdown:
        **bold**, *italic*, # heading, - list, [link](url).
    </p>
    <p class="status">
        Public display is currently showing: {displayMode === 'message' ? 'this message' : 'the live lot/buyer display'}
    </p>
    <button class="toggle-btn" on:click={handleToggle} disabled={saving}>
        {displayMode === 'message' ? 'Show Lot Display' : 'Show Message Screen'}
    </button>

    <textarea bind:value={draftMessage} placeholder="e.g. The auction will begin at 6:00 PM. Thank you for joining us!"></textarea>
    <button class="save-btn" on:click={handleSave} disabled={saving}>Save Message</button>

    <p class="preview-label">Preview</p>
    <div class="preview">{@html renderMarkdown(draftMessage)}</div>
</div>
