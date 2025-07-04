#!/usr/bin/env node
/**
 * Test dashboard data loading
 */
const https = require('https');

// Test direct Supabase API call similar to what dashboard does
const SUPABASE_URL = 'https://fycatruiawynbzuafdsx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5Y2F0cnVpYXd5bmJ6dWFmZHN4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTk5MzI2NjksImV4cCI6MjAzNTUwODY2OX0.z8hfoI29aHdVB2wNrNhDLEhBSt7nFJ5wSlMLNWgOqPw';

const options = {
    hostname: 'fycatruiawynbzuafdsx.supabase.co',
    port: 443,
    path: '/rest/v1/tenders?select=*&order=extracted_at.desc&limit=10',
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'apikey': SUPABASE_ANON_KEY,
        'Content-Type': 'application/json'
    }
};

console.log('🧪 Testing dashboard data loading...');
console.log('📡 Making API call to Supabase...');

const req = https.request(options, (res) => {
    let data = '';
    
    res.on('data', (chunk) => {
        data += chunk;
    });
    
    res.on('end', () => {
        try {
            const tenders = JSON.parse(data);
            console.log(`✅ Successfully loaded ${tenders.length} tenders`);
            
            if (tenders.length > 0) {
                console.log('\n📊 Sample tenders:');
                tenders.slice(0, 3).forEach((tender, i) => {
                    console.log(`   ${i+1}. ${tender.title.substring(0, 50)}...`);
                    console.log(`      Country: ${tender.country} | Source: ${tender.source} | Score: ${tender.relevance_score}`);
                });
                
                // Calculate stats like dashboard does
                const total = tenders.length;
                const ungmCount = tenders.filter(t => t.source === 'UNGM').length;
                const tunipagesCount = tenders.filter(t => t.source === 'TUNIPAGES').length;
                const avgScore = (tenders.reduce((sum, t) => sum + (t.relevance_score || 0), 0) / total).toFixed(1);
                
                console.log('\n📈 Dashboard stats:');
                console.log(`   Total: ${total} | UNGM: ${ungmCount} | TuniPages: ${tunipagesCount} | Avg Score: ${avgScore}`);
                console.log('\n🎉 Dashboard data loading is working correctly!');
            } else {
                console.log('⚠️ No tenders found in database');
            }
        } catch (err) {
            console.error('❌ Error parsing response:', err.message);
            console.log('Raw response:', data);
        }
    });
});

req.on('error', (err) => {
    console.error('❌ API request failed:', err.message);
});

req.end();