/**
 * download-models.js
 * Run once: node download-models.js
 * Downloads face-api.js model files needed for blink detection.
 * Files are saved to: public/models/
 */

import { createWriteStream, mkdirSync } from 'fs'
import { get }  from 'https'
import { join } from 'path'

const BASE_URL  = 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights'
const OUT_DIR   = join(process.cwd(), 'public', 'models')

mkdirSync(OUT_DIR, { recursive: true })

const FILES = [
  // Tiny face detector
  'tiny_face_detector_model-weights_manifest.json',
  'tiny_face_detector_model-shard1',
  // Tiny 68-point landmark model (used with withFaceLandmarks(true))
  'face_landmark_68_tiny_model-weights_manifest.json',
  'face_landmark_68_tiny_model-shard1',
]

function download(filename) {
  return new Promise((resolve, reject) => {
    const url  = `${BASE_URL}/${filename}`
    const dest = join(OUT_DIR, filename)
    const file = createWriteStream(dest)

    process.stdout.write(`  ⬇  ${filename} … `)

    get(url, (res) => {
      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode} for ${url}`))
        return
      }
      res.pipe(file)
      file.on('finish', () => {
        file.close()
        console.log('✓')
        resolve()
      })
    }).on('error', reject)
  })
}

console.log('\n🧠  Downloading face-api.js model weights...\n')

for (const f of FILES) {
  try {
    await download(f)
  } catch (err) {
    console.error(`\n  ✗ Failed: ${err.message}`)
    process.exit(1)
  }
}

console.log('\n✅  All models saved to public/models/\n')
console.log('   You can now run: npm run dev\n')
