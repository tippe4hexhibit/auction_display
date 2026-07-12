<script>
    import { THEMES, DEFAULT_THEME } from '../themes.js';
    import { makeAuthenticatedRequest } from '../utils/auth.js';

    export let currentTheme = DEFAULT_THEME;

    const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
    let saving = false;

    async function applyTheme(name) {
        if (name === currentTheme || saving) return;
        saving = true;
        try {
            const response = await makeAuthenticatedRequest(`${API_BASE}/api/theme`, {
                method: 'POST',
                body: JSON.stringify({ theme: name })
            });
            if (!response.ok) {
                const error = await response.json();
                alert(`Failed to update theme: ${error.detail}`);
            }
        } catch (error) {
            alert('Failed to update theme: ' + error.message);
        } finally {
            saving = false;
        }
    }
</script>

<style>
    .theme-picker {
        margin: 1rem 0;
        padding: 1rem;
        border: 1px solid #ccc;
        border-radius: 8px;
        background: #f9f9f9;
    }
    .theme-picker h3 { margin-top: 0; }
    .hint { margin: 0 0 0.75rem 0; font-size: 0.9rem; color: #555; }
    .swatches { display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center; }
    .swatch {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.9rem;
        border: 2px solid #ccc;
        border-radius: 6px;
        cursor: pointer;
        background: white;
        font: inherit;
    }
    .swatch:disabled { cursor: not-allowed; opacity: 0.6; }
    .swatch.active { border-color: #007bff; font-weight: bold; }
    .swatch-preview {
        width: 1.1rem;
        height: 1.1rem;
        border-radius: 50%;
        flex-shrink: 0;
        /* Fixed neutral ring so the dot stays visible even for themes
           whose own border/header colors are white (e.g. solid presets
           with an inverted header) — never rely on theme colors here. */
        border: 2px solid rgba(0, 0, 0, 0.35);
        box-sizing: border-box;
    }
    .reset-btn {
        margin-left: auto;
        padding: 0.5rem 0.9rem;
        border-radius: 6px;
        border: 1px solid #dc3545;
        background: white;
        color: #dc3545;
        cursor: pointer;
        font: inherit;
    }
    .reset-btn:disabled { cursor: not-allowed; opacity: 0.6; }
    .reset-btn:hover:not(:disabled) { background: #dc3545; color: white; }
</style>

<div class="theme-picker">
    <h3>Public Display Theme</h3>
    <p class="hint">Changes apply instantly to the public display. If a preset is hard to read on your projector, just click Reset.</p>
    <div class="swatches">
        {#each Object.entries(THEMES) as [name, theme]}
            <button
                type="button"
                class="swatch"
                class:active={currentTheme === name}
                on:click={() => applyTheme(name)}
                disabled={saving}
            >
                <span class="swatch-preview" style="background: {theme.background};"></span>
                {theme.label}
            </button>
        {/each}
        <button
            type="button"
            class="reset-btn"
            on:click={() => applyTheme(DEFAULT_THEME)}
            disabled={saving || currentTheme === DEFAULT_THEME}
        >
            Reset to Default
        </button>
    </div>
</div>
