#!/usr/bin/env node
import { execSync } from 'child_process';
import { readFileSync, writeFileSync, existsSync, unlinkSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const frontendDir = join(__dirname, '..');
const netlifyToml = join(frontendDir, 'netlify.toml');
const netlifyLocalToml = join(frontendDir, 'netlify.local.toml');
const netlifyTomlBackup = join(frontendDir, 'netlify.toml.backup');

// Check if local config exists
if (!existsSync(netlifyLocalToml)) {
  console.error('Error: netlify.local.toml not found');
  process.exit(1);
}

// Backup original config
const originalConfig = readFileSync(netlifyToml, 'utf8');
writeFileSync(netlifyTomlBackup, originalConfig, 'utf8');

try {
  // Copy local config to main config
  const localConfig = readFileSync(netlifyLocalToml, 'utf8');
  writeFileSync(netlifyToml, localConfig, 'utf8');
  
  console.log('Using local API configuration (http://localhost:8080)');
  console.log('Starting Netlify Dev...\n');
  
  // Run netlify dev
  execSync('netlify dev', {
    cwd: frontendDir,
    stdio: 'inherit',
    shell: true
  });
} catch (error) {
  // If it's not an exit code error, rethrow
  if (error.status === undefined && error.code !== 'ENOENT') {
    throw error;
  }
  // Otherwise, netlify dev was interrupted (Ctrl+C), which is fine
} finally {
  // Always restore original config
  if (existsSync(netlifyTomlBackup)) {
    writeFileSync(netlifyToml, originalConfig, 'utf8');
    // Remove backup file
    try {
      unlinkSync(netlifyTomlBackup);
    } catch (e) {
      // Ignore errors removing backup
    }
  }
}

