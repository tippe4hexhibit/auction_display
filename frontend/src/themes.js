// Keep these keys in sync with ALLOWED_THEMES in backend/database.py.
// Most presets keep body text black-on-white so the bidder list is always
// readable at a distance, with color limited to borders/headers. Solid
// presets (like fourh_green_solid) are the deliberate exception; verify
// their background/text contrast ratio meets WCAG AA (>= 3:1 for this
// display's large text) before adding another one.
// swatchColor is only for the admin picker's preview dot — it's the
// preset's "brand color" and is independent of background/headerBg,
// since which of those is the colorful one varies (e.g. fourh_green
// colors its header, fourh_green_solid inverts the header to white
// and colors the page background instead).
export const THEMES = {
    classic: {
        label: 'Classic (Black & White)',
        background: '#ffffff',
        text: '#000000',
        borderColor: '#000000',
        headerBg: '#ffffff',
        headerText: '#000000',
        tableHeaderBg: '#f0f0f0',
        separatorColor: '#999999',
        swatchColor: '#ffffff'
    },
    fourh_green: {
        label: '4-H Green',
        background: '#ffffff',
        text: '#000000',
        borderColor: '#00843D',
        headerBg: '#00843D',
        headerText: '#ffffff',
        tableHeaderBg: '#e6f4ec',
        separatorColor: '#00843D',
        swatchColor: '#00843D'
    },
    fourh_green_solid: {
        // #00843D vs white text ≈ 4.8:1 contrast — clears WCAG AA for
        // normal text, not just the 3:1 large-text minimum.
        label: '4-H Green (Solid)',
        background: '#00843D',
        text: '#ffffff',
        borderColor: '#ffffff',
        headerBg: '#ffffff',
        headerText: '#00843D',
        tableHeaderBg: '#00612E',
        separatorColor: '#ffffff',
        swatchColor: '#00843D'
    },
    high_contrast: {
        label: 'High Contrast (Black & Yellow)',
        background: '#000000',
        text: '#ffffff',
        borderColor: '#FFD200',
        headerBg: '#000000',
        headerText: '#FFD200',
        tableHeaderBg: '#222222',
        separatorColor: '#FFD200',
        swatchColor: '#000000'
    }
};

export const DEFAULT_THEME = 'classic';
