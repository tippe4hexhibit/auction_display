// Keep these keys in sync with ALLOWED_THEMES in backend/database.py.
// Body text stays black-on-white in every preset so the bidder list is
// always readable at a distance; color is limited to borders/headers.
export const THEMES = {
    classic: {
        label: 'Classic (Black & White)',
        background: '#ffffff',
        text: '#000000',
        borderColor: '#000000',
        headerBg: '#ffffff',
        headerText: '#000000',
        tableHeaderBg: '#f0f0f0',
        separatorColor: '#999999'
    },
    fourh_green: {
        label: '4-H Green',
        background: '#ffffff',
        text: '#000000',
        borderColor: '#00843D',
        headerBg: '#00843D',
        headerText: '#ffffff',
        tableHeaderBg: '#e6f4ec',
        separatorColor: '#00843D'
    },
    high_contrast: {
        label: 'High Contrast (Black & Yellow)',
        background: '#000000',
        text: '#ffffff',
        borderColor: '#FFD200',
        headerBg: '#000000',
        headerText: '#FFD200',
        tableHeaderBg: '#222222',
        separatorColor: '#FFD200'
    }
};

export const DEFAULT_THEME = 'classic';
