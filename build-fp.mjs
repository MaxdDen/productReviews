// build-fp.js
import { promises as fs } from 'fs';
import FingerprintJS from '@fingerprintjs/fingerprintjs';

const fpCode = `
  window.FingerprintJS = FingerprintJS;
`;

await fs.writeFile(
  'app/static/js/fingerprint.js',
  fpCode,
  'utf-8'
);
