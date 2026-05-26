// ───────────────────────────────────────────────────────────────────────────
// Document reader (OCR → lines / table).
//
// Reads an uploaded image or PDF with Tesseract.js.  Images are PRE-PROCESSED
// (upscaled + grayscale + contrast-stretched) before OCR — this matters a lot
// for phone photos of faint/low-contrast documents.  PDFs are rasterized with
// pdf.js first.
//
// Returns both a readable line-by-line view and a best-effort column grid:
//   const r = await window.DocumentReader.read(file, { onProgress });
//   // r = { lines: string[], table: { rows: string[][], cols }, text, pages }
//
// Depends on global Tesseract + pdfjsLib (loaded by index.html). Exposes
// window.DocumentReader.
// ───────────────────────────────────────────────────────────────────────────
(function () {
    let pdfWorkerSet = false;
    let currentProgress = function () {};

    const FIELD_DEFS = [
        { key: "Plate Number",    row: /pla?te?\s*e?n[o0]/i,      kw: /^pla/i },
        { key: "Engine Number",   row: /eng\w*\s*n[o0]/i,         kw: /^eng/i },
        { key: "Brand",           row: /make|brand/i,             kw: /make|brand/i },
        { key: "Color",           row: /colou?r/i,                kw: /colou?r/i },
        { key: "Model",           row: /series/i,                 kw: /series/i },
        { key: "Displacement",    row: /displacement/i,           kw: /piston|displacement/i },
        { key: "Owner's Name",    row: /owner.{0,4}\s*name/i,     kw: /owner/i, fullWidth: true },
        { key: "Owner's Address", row: /owner.{0,4}\s*address/i,  kw: /owner/i, fullWidth: true },
    ];

    function ensurePdfWorker() {
        if (pdfWorkerSet) return;
        if (window.pdfjsLib && window.pdfjsLib.GlobalWorkerOptions) {
            window.pdfjsLib.GlobalWorkerOptions.workerSrc =
                "https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js";
            pdfWorkerSet = true;
        }
    }

    function ocr(source) {
        return window.Tesseract.recognize(source, "eng", {
            logger: (m) => {
                if (m.status === "recognizing text" && typeof m.progress === "number") {
                    currentProgress(m.progress, "Recognizing text… " + Math.round(m.progress * 100) + "%");
                } else if (m.status) {
                    currentProgress(null, m.status);
                }
            },
        }).then(({ data }) => data);
    }

    function readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const r = new FileReader();
            r.onload = () => resolve(r.result);
            r.onerror = reject;
            r.readAsArrayBuffer(file);
        });
    }

    function loadImage(url) {
        return new Promise((resolve, reject) => {
            const im = new Image();
            im.onload = () => resolve(im);
            im.onerror = reject;
            im.src = url;
        });
    }

    function preprocess(source) {
        const sw = source.naturalWidth || source.width;
        const sh = source.naturalHeight || source.height;
        const scale = sw && sw < 1400 ? 2 : 1;
        const w = Math.max(1, Math.round(sw * scale));
        const h = Math.max(1, Math.round(sh * scale));

        const canvas = document.createElement("canvas");
        canvas.width = w; canvas.height = h;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(source, 0, 0, w, h);

        const imgData = ctx.getImageData(0, 0, w, h);
        const d = imgData.data;

        const gray = new Uint8ClampedArray(d.length / 4);
        const hist = new Array(256).fill(0);
        for (let i = 0, p = 0; i < d.length; i += 4, p++) {
            const g = (d[i] * 0.299 + d[i + 1] * 0.587 + d[i + 2] * 0.114) | 0;
            gray[p] = g;
            hist[g]++;
        }

        const total = gray.length;
        let acc = 0, lo = 0, hi = 255;
        for (let i = 0; i < 256; i++) { acc += hist[i]; if (acc >= total * 0.02) { lo = i; break; } }
        acc = 0;
        for (let i = 255; i >= 0; i--) { acc += hist[i]; if (acc >= total * 0.02) { hi = i; break; } }
        const range = Math.max(1, hi - lo);

        for (let p = 0, i = 0; p < gray.length; p++, i += 4) {
            let v = ((gray[p] - lo) / range) * 255;
            v = Math.max(0, Math.min(255, v));
            v = Math.pow(v / 255, 1.25) * 255;
            d[i] = d[i + 1] = d[i + 2] = v;
            d[i + 3] = 255;
        }
        ctx.putImageData(imgData, 0, 0);
        return canvas;
    }

    async function pdfToCanvases(arrayBuffer, onProgress) {
        ensurePdfWorker();
        const pdf = await window.pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        const canvases = [];
        for (let i = 1; i <= pdf.numPages; i++) {
            onProgress(null, `Rendering page ${i}/${pdf.numPages}…`);
            const page = await pdf.getPage(i);
            const viewport = page.getViewport({ scale: 2 });
            const canvas = document.createElement("canvas");
            canvas.width = viewport.width; canvas.height = viewport.height;
            await page.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
            canvases.push(canvas);
        }
        return canvases;
    }

    function lineWordsFromData(data) {
        let lines = [];
        if (Array.isArray(data.lines) && data.lines.length) {
            lines = data.lines;
        } else if (Array.isArray(data.blocks)) {
            data.blocks.forEach((b) =>
                (b.paragraphs || []).forEach((p) =>
                    (p.lines || []).forEach((l) => lines.push(l))));
        }
        return lines
            .map((line) => (line.words || [])
                .filter((w) => (w.text || "").trim())
                .map((w) => ({ text: w.text.trim(), x0: w.bbox.x0, x1: w.bbox.x1 })))
            .filter((arr) => arr.length);
    }

    function pad(arr, n) {
        const out = arr.slice();
        while (out.length < n) out.push("");
        return out;
    }

    function linesText(data) {
        const lw = lineWordsFromData(data);
        if (lw.length) return lw.map((words) => words.map((w) => w.text).join(" "));
        return (data.text || "").split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    }

    function allWords(data) {
        let lines = [];
        if (Array.isArray(data.lines) && data.lines.length) {
            lines = data.lines;
        } else if (Array.isArray(data.blocks)) {
            data.blocks.forEach((b) =>
                (b.paragraphs || []).forEach((p) =>
                    (p.lines || []).forEach((l) => lines.push(l))));
        }
        const words = [];
        lines.forEach((l) => (l.words || []).forEach((w) => {
            const t = (w.text || "").trim();
            if (t) words.push({ text: t, x0: w.bbox.x0, x1: w.bbox.x1, y0: w.bbox.y0, y1: w.bbox.y1 });
        }));
        return words;
    }

    function buildTable(data) {
        const words = allWords(data);
        if (!words.length) {
            const rows = (data.text || "").split(/\r?\n/).map((l) => l.trim())
                .filter(Boolean).map((l) => l.split(/\s{2,}/));
            const cols = rows.reduce((m, r) => Math.max(m, r.length), 0) || 1;
            return { rows: rows.map((r) => pad(r, cols)), cols };
        }

        const maxX = Math.max.apply(null, words.map((w) => w.x1));
        const heights = words.map((w) => w.y1 - w.y0).sort((a, b) => a - b);
        const medH = heights[Math.floor(heights.length / 2)] || 12;
        const widths = words.map((w) => w.x1 - w.x0).sort((a, b) => a - b);
        const medW = widths[Math.floor(widths.length / 2)] || 18;

        const yTol = medH * 0.7;
        const byY = words.slice().sort((a, b) => ((a.y0 + a.y1) / 2) - ((b.y0 + b.y1) / 2));
        const rows = [];
        let cur = [], curY = null;
        byY.forEach((w) => {
            const yc = (w.y0 + w.y1) / 2;
            if (curY === null || Math.abs(yc - curY) <= yTol) {
                cur.push(w);
                curY = curY === null ? yc : (curY * (cur.length - 1) + yc) / cur.length;
            } else {
                rows.push(cur); cur = [w]; curY = yc;
            }
        });
        if (cur.length) rows.push(cur);

        const tol = Math.max(maxX * 0.045, medW * 1.5);
        const xs = words.map((w) => w.x0).sort((a, b) => a - b);
        const clusters = [];
        xs.forEach((x) => {
            const last = clusters[clusters.length - 1];
            if (last && x - last.mean <= tol) {
                last.sum += x; last.n += 1; last.mean = last.sum / last.n;
            } else {
                clusters.push({ sum: x, n: 1, mean: x });
            }
        });
        const minSupport = Math.max(2, Math.round(rows.length * 0.2));
        let anchors = clusters.filter((c) => c.n >= minSupport).map((c) => c.mean);
        if (anchors.length < 2) anchors = clusters.map((c) => c.mean);
        anchors.sort((a, b) => a - b);

        const colOf = (w) => {
            let idx = 0;
            for (let i = 0; i < anchors.length; i++) {
                if (w.x0 >= anchors[i] - tol) idx = i; else break;
            }
            return idx;
        };

        const grid = rows.map((rowWords) => {
            const cells = Array.from({ length: anchors.length }, () => []);
            rowWords.slice().sort((a, b) => a.x0 - b.x0).forEach((w) => cells[colOf(w)].push(w.text));
            return cells.map((c) => c.join(" "));
        }).filter((r) => r.some((c) => c.trim()));

        return { rows: grid, cols: anchors.length };
    }

    function clusterRows(data) {
        return buildTable(data);
    }

    function extractFields(lines) {
        const rows = lines.map((line) => ({ text: line, upper: line.toUpperCase() }));
        const fields = {};

        FIELD_DEFS.forEach((field) => {
            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];
                if (field.row.test(row.text)) {
                    const nextLine = rows[i + 1] ? rows[i + 1].text.trim() : "";
                    if (field.fullWidth) {
                        fields[field.key] = nextLine || row.text.replace(field.row, "").trim();
                    } else {
                        const match = row.text.match(field.row);
                        if (match) {
                            const rest = row.text.slice(match.index + match[0].length).replace(/[:\-]+$/, "").trim();
                            fields[field.key] = rest || nextLine;
                        }
                    }
                    break;
                }
            }
        });

        return fields;
    }

    function analyze(data) {
        const lines = linesText(data);
        const table = clusterRows(data);
        return { text: lines.join("\n"), lines, table, fields: extractFields(lines) };
    }

    window.DocumentReader = { read: async function(file, opts) {
        opts = opts || {};
        currentProgress = opts.onProgress || function () {};
        const isPdf = file.type === "application/pdf" || /\.pdf$/i.test(file.name);
        const sources = isPdf ? await pdfToCanvases(await readFileAsArrayBuffer(file), currentProgress) : [await loadImage(URL.createObjectURL(file))];
        const pages = [];
        for (let i = 0; i < sources.length; i++) {
            currentProgress(null, `Preprocessing page ${i + 1}/${sources.length}…`);
            const prepared = preprocess(sources[i]);
            currentProgress(null, `Recognizing text on page ${i + 1}/${sources.length}…`);
            const data = await ocr(prepared);
            pages.push(data);
        }
        const merged = { text: pages.map((p) => p.text).join("\n"), lines: [], blocks: [] };
        pages.forEach((p) => {
            if (Array.isArray(p.lines)) merged.lines.push(...p.lines);
            if (Array.isArray(p.blocks)) merged.blocks.push(...p.blocks);
        });
        return analyze(merged);
    } };
})();
