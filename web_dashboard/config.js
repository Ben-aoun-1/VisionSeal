// VisionSeal Configuration
// This file should be served from backend with proper environment variables
// DO NOT store credentials here in production

window.VISIONSEAL_CONFIG = {
    // These should be replaced by backend template rendering
    SUPABASE_URL: '{{SUPABASE_URL}}',
    SUPABASE_ANON_KEY: '{{SUPABASE_ANON_KEY}}',
    
    // Default fallback for development (replace with actual values)
    DEV_SUPABASE_URL: 'https://fycatruiawynbzuafdsx.supabase.co',
    DEV_SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5Y2F0cnVpYXd5bmJ6dWFmZHN4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE0OTY5ODksImV4cCI6MjA2NzA3Mjk4OX0.GuCF6lUiZKr23mCgqGw42uamp6qME4v8Ip6CR0Fn9fw'
};

// Helper function to get config values
function getSupabaseConfig() {
    const config = window.VISIONSEAL_CONFIG;
    
    // Check if values are templated (production)
    if (config.SUPABASE_URL && !config.SUPABASE_URL.includes('{{')) {
        return {
            url: config.SUPABASE_URL,
            anonKey: config.SUPABASE_ANON_KEY
        };
    }
    
    // Fallback to dev values (development only)
    return {
        url: config.DEV_SUPABASE_URL,
        anonKey: config.DEV_SUPABASE_ANON_KEY
    };
}